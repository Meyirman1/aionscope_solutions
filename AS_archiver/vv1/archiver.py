##AUTOMATING dest_paths with pathlib
##                    THE GLOSSARY FOR SHORTED WORDS:
## fp (filepath).
## lv (local view)

import json
from pathlib import Path 
import pydicom
from datetime import datetime
# import logging ##pip install
# import sentry ##pip install
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import setup_db
import sqlite3

#Building first Path folders so when it return none it doesn't nulify the address.

src_dir = Path('reports_receiver')
#contains original txt/dcm reports

lv_dir = Path('local_view')

# parent for those below sub dirs 
lv_reports = Path(lv_dir/'REPORTS')
lv_meta = Path(lv_dir/'METADATA')

arch_reports_dir = Path.home()/'REPORTS_META_BACKUP'/'ARCHIVED_REPORTS'
#contains copy of original reports as original reports inside archived dir
meta_dir = Path.home()/'REPORTS_META_BACKUP'/'ARCHIVED_METADATA'
#contains json files with metadata inside archived dir

all_dirs = [src_dir,meta_dir,arch_reports_dir,lv_dir,lv_reports,lv_meta]
for each_dir in all_dirs:
    each_dir.mkdir(parents=True, exist_ok=True)

src_reports = list(src_dir.glob('*.txt'))
#puts all file format in one list.
src_dcm_reports = list(src_dir.glob('*.dcm'))



def log_to_db(data, db_path = setup_db.db_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql = ("""
           INSERT OR IGNORE into reports
            (patient_id, patient_name, report_name, filter_type, report_date, modality,  file_path, archived_at)
           VALUES (?,?,?,?,?,?,?,?)
    """)
    datenow = datetime.now()
    #timestamp = datenow.strftime("%d-%m-%Y, %H:%M:%S")
         ##formatted but due to computer could have misconception 
         ##when displaying recent reports so use Y/M/D format.
    timestamp = datenow.strftime("%Y-%m-%d, %H:%M:%S")
    values = (
       data['patient_id'],
       data['patient_name'],
       data['report_name'],
       data['filter_type'],
       data['report_date'],
       data['modality'],
       str(data['file_path']),
       timestamp
    )

    try:
        cursor.execute(sql, values)
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✅ Database updated for Patient: {data['patient_id']}")
        else:
            print(f"⚠️ Skip: File already indexed in database.")
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

def extract_metadata(patient_id,report_name,report_type,report_date,patient_name,modality, file_path):
    extract  = {
        "patient_id": f"P{patient_id}",
        "report_name": f"{report_name}",
        #report name could be for ex (knee234.dcm , tumourJ34.dcm)
        "filter_type": f"{report_type}",  
        "report_date": f"{report_date}",
        "patient_name": f"{patient_name}",
        "modality": f"{modality}",
        "file_path": f"{file_path}",
                 }
    return extract

def arch_reports(orig_reports):
    try:
        for orig_report in orig_reports:
            stemmed = orig_report.stem
            #stem only takes a name of the file without .txt
            parts = stemmed.split('_')
            

            if not len(parts) == 6:
                print(f"⚠️  [RENAME REQUIRED]: File '{orig_report.name}' lacks the correct metadata format.")
                print("\tFormat must be: type_ID_date_Firstname_Lastname_modality.txt")
                return False # Stops the function and tells safe_archive NOT to delete
                    
            report_type = parts[0]
            patient_id = parts[1]
            report_date = parts[2]
            patient_firstname = parts[3]
            patient_lastname = parts[4]
            patient_name = ' '.join([patient_firstname, patient_lastname])
            modality = parts[-1]
            
            metadata_json = orig_report.with_suffix('.json')
            #swaps existing 'txt' with json and only creates a new path name in PYTHON.
            # replace(string method) has more risks to not cut exact 'report.txt.leichomia.txt' but the name so use this above.

            lv_dest_report_fp = lv_reports/orig_report.name
            lv_dest_meta_fp = lv_meta/metadata_json.name
    
            dest_report_fp = arch_reports_dir/orig_report.name
            dest_meta_fp = meta_dir/metadata_json.name
            # .name only returns 'report.txt' 
            # (orig report returns the file with its parent directory 'report_samples/report.txt')

            # report_name = orig_report.name
            payload_metadata = extract_metadata(patient_id,orig_report.name,report_type,report_date,patient_name,modality,dest_report_fp)

            report_text = orig_report.read_text()
            dest_report_fp.write_text(report_text)
            lv_dest_report_fp.write_text(report_text)
            print(f"✅The report with ID:{parts[1]} was archived successfully!")
                    
            with open(dest_meta_fp, 'w') as json_ouput:
                json_dest = json_ouput
                json.dump(payload_metadata, json_dest, indent=4)
            with open(lv_dest_meta_fp, 'w') as lv_json_output:
                lv_json_dest = lv_json_output
                json.dump(payload_metadata,lv_json_dest, indent=4)
         
            log_to_db(payload_metadata, setup_db.db_name)
            #INSERTING TO SQLITE3 DB
            
            return True # SUCCESS: Tells safe_archive it is safe to delete original
    except FileNotFoundError:
        print("\tERROR: Check if the targeted filepaths are correct.".upper())
    except Exception as e:
        print(f"[X] Error during archival: {e}")
        return False
  
            
    
def extract_dcm_header(dcm_report,report_name,filepath):
    get_id = dcm_report.get('PatientID','UnknownPatientID')
    get_date = dcm_report.get('ContentDate') or dcm_report.get('AcquisitionDate') or dcm_report.get('StudyDate') or dcm_report.get('InstanceCreationDate')
    get_name = dcm_report.get('PatientName','UnknownPatientName')
    get_filter_type = dcm_report.get('FilterType','UnknownPatientReportType')
    get_sex = dcm_report.get('PatientSex','UnknownPatientSex')
    get_si_uid = dcm_report.get('StudyInstanceUID','UnknownStudyInstanceUID')
    get_modality = dcm_report.get('Modality','UnknownModality')
    # get_report_name = dcm_report.get('StudyDescription', )
    if get_date and str(get_date).isdigit():
        try:
            format_date = datetime.strptime(get_date,"%Y%m%d").strftime("%d-%m-%Y")
        except(TypeError,ValueError):
            format_date = 'Corrupted Date'
    else:
        format_date = 'UnknownDate'   

    format_name = str(get_name).replace("^"," ")
    format_id = str(get_id).strip()
    #made id string
    extract  = {
        "patient_id": f"P{format_id}",
        "report_name": f"{report_name}",
        "report_date": f"{format_date}",
        "patient_name": f"{format_name}",
        "filter_type": f"{get_filter_type}",
        "patient_gender": f"{get_sex}",
        "study Instance UID": f"{get_si_uid}",
        "modality": f"{get_modality}",
        "file_path": f"{filepath}",
                 }
    return extract

def arch_dcm_reports(dcm_reports):
    try:
        for dcm_report in dcm_reports:
            header_json = dcm_report.with_suffix('.json')

            lv_dest_report_fp = lv_reports/dcm_report.name
            lv_dest_meta_fp = lv_meta/header_json.name

            dest_report_fp = arch_reports_dir / dcm_report.name
            dest_meta_fp = meta_dir/header_json.name

            ds = pydicom.dcmread(dcm_report, force=True)
            ds.save_as(dest_report_fp)
            ds.save_as(lv_dest_report_fp)
            cleaned_dcm = dcm_report.with_suffix('').name
            patient_id = ds.get("PatientID","Anonymized")
            print(f"✅ The report {cleaned_dcm} with ID:{patient_id} was archived successfully!")

            payload_header = extract_dcm_header(ds,dcm_report.name,dest_report_fp)

            with open(dest_meta_fp, "w") as f_obj:
                dcm_header = f_obj
                json.dump(payload_header, dcm_header, indent=4)
            with open(lv_dest_meta_fp, "w") as f_obj:
                lv_dcm_header = f_obj
                json.dump(payload_header, lv_dcm_header, indent=4)
            log_to_db(payload_header, setup_db.db_name)
            return True
    except FileNotFoundError:
        print("\tERROR: Check if the targeted filepaths are correct.".upper())
        return False
    
def safe_archive(file_path):
    retries = 5
    while retries > 0:
        try:
            status = False
            if file_path.suffix.lower() == '.txt':
                status = arch_reports([file_path])
               
                if status and file_path:
                    print(f"[OK] Cleaning up the source {file_path.name} from {src_dir}")
                    file_path.unlink()
                    return True
                else:
                    print(f"🛑 [HOLD] {file_path.name} preserved. Please fix the filename underscores.")
                    return False
            elif file_path.suffix.lower() == '.dcm':
                status = arch_dcm_reports([file_path])
                  
                if status:
                    print(f"[OK] Cleaning up DICOM: {file_path.name}")
                    file_path.unlink()
                    return True
                else:
                    print(f"🛑 [HOLD] DICOM {file_path.name} failed processing.")
                    return False
           
        except IsADirectoryError:
                #for extra backup safety
                print(f"   [!] File {file_path.name} is a folder, Please extract file-reports and delete the folder to proceed the successful archival.")
                break
        
        except PermissionError:
            print(f"   [!] File {file_path.name} is busy. Retrying in 1s... ({retries} left)")
            time.sleep(1)
            retries -= 1

        except Exception as e:
            print(f"   [!] Critical error on {file_path} {type(e).__name__} - {e}")
            break

    print(f"   [X] FAILED to archive {file_path.name} after multiple attempts.")

class ReportHandler(FileSystemEventHandler):
   def on_created(self, event):
    ##Checking if event is just a folder if True it ignores it with 'return'
    if event.is_directory:
        return 
    try:   
        raw_path = str(event.src_path)
        file_path = Path(raw_path).resolve()
        ## get the actual name of the file is just created
        print(f"\nDetected new file and is being processed: {file_path.name}") 
        
        safe_archive(file_path)

    except Exception as e:
        print(f"[!] ERROR processing {str(event.src_path)}: {e}")

observer = Observer()
##Observer creation is the guard
handler = ReportHandler()

observer.schedule(handler, path=str(src_dir), recursive=False)
##Giving the guard the manual(handler)

print(f"\nPerforming scan for leftover files in '{src_dir}' directory:")
leftovers = list(src_dir.glob('*'))
process_count = 0
for left_report in leftovers:
    if left_report.is_file():
        safe_archive(left_report)
        process_count += 1
    elif left_report.is_dir():  
        print(f"   [!] Please extract file-report(s) and delete the folder '{left_report.name}' to proceed a successful archival.")
        process_count += 1
if process_count == 0:
        print("\tNo leftover file-reports to process were found.")

observer.start()
##start the guard shift

print("-" * 36)
print("Watching the folder for new reports:")
print("-" * 36)
try:
    while True:
        time.sleep(0.5)
    # The script "sleeps" for 1 second, then loops again.
    # This uses almost zero CPU power.
except KeyboardInterrupt:
    observer.stop()

observer.join()
# Wait for the guard to finish packing up before closing completely.





    
       
          



