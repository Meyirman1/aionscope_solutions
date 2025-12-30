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

#Building first folders so when it return none it doesn't nulify the address.

src_dir = Path('report_samples')
#contains original txt reports

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

def extract_metadata(patient_id,date,patient_fname,patient_lname,modality):
    extract  = {
        "patient_id": f"P{patient_id}",
        "date": f"{date}",
        "patient_firstname": f"{patient_fname}",
        "patient_lastname": f"{patient_lname}",
        "modality": f"{modality}"
                 }
    return extract

def arch_reports(orig_reports):
    try:
        for orig_report in orig_reports:
            parts = orig_report.stem.split('_')
            patient_id = parts[1]
            date = parts[2]
            patient_fname = parts[3]
            patient_lname = parts[4]
            modality = parts[-1]

            payload_metadata = extract_metadata(patient_id,date,patient_fname,patient_lname,modality)

            metadata_json = orig_report.with_suffix('.json')
            #swaps existing 'txt' with json and only creates a new path name in PYTHON.
            # replace(string method) has more risks to not cut exact 'report.txt.leichomia.txt' but the name so use this above.

            lv_dest_report_fp = lv_reports/orig_report.name
            lv_dest_meta_fp = lv_meta/metadata_json.name
    
            dest_report_fp = arch_reports_dir/orig_report.name
            dest_meta_fp = meta_dir/metadata_json.name
            # .name only returns 'report.txt' 
            # (orig report returns the file with its parent directory 'report_samples/report.txt')

            # local_view_fp = view_dir / orig_report.name
            
            report_text = orig_report.read_text()
            dest_report_fp.write_text(report_text)
            lv_dest_report_fp.write_text(report_text)
            print(f"The report with ID:{parts[1]} was archived successfully!")
                    
            with open(dest_meta_fp, 'w') as json_ouput:
                json_dest = json_ouput
                json.dump(payload_metadata, json_dest, indent=4)
            with open(lv_dest_meta_fp, 'w') as lv_json_output:
                lv_json_dest = lv_json_output
                json.dump(payload_metadata,lv_json_dest, indent=4)
    except FileNotFoundError:
        print("\tERROR: Check if the targeted filepaths are correct.".upper())
    
def extract_dcm_header(dcm_report):
    get_id = dcm_report.get('PatientID','UnknownPatientID')
    get_date = dcm_report.get('ContentDate') or dcm_report.get('AcquisitionDate') or dcm_report.get('StudyDate') or dcm_report.get('InstanceCreationDate')
    get_name = dcm_report.get('PatientName','UnknownPatientName')
    get_sex = dcm_report.get('PatientSex','UnknownPatientSex')
    get_si_uid = dcm_report.get('StudyInstanceUID','UnknownStudyInstanceUID')
    get_modality = dcm_report.get('Modality','UnknownModality')
    
    if get_date and str(get_date).isdigit():
        try:
            format_date = datetime.strptime(get_date,"%Y%m%d").strftime("%d-%m-%Y")
        except(TypeError,ValueError):
            format_date = 'Corrupted Date'
    else:
        format_date = 'UnknownDate'   

    format_name = str(get_name).replace("^"," ")

    extract  = {
        "patient_id": f"P{get_id}",
        "date": f"{format_date}",
        "patient_name": f"{format_name}",
        "patient_gender": f"{get_sex}",
        "study Instance UID": f"{get_si_uid}",
        "modality": f"{get_modality}"
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
            print(f"The report {cleaned_dcm} with ID:{patient_id} was archived successfully!")

            payload_header = extract_dcm_header(ds)

            with open(dest_meta_fp, "w") as f_obj:
                dcm_header = f_obj
                json.dump(payload_header, dcm_header, indent=4)
            with open(lv_dest_meta_fp, "w") as f_obj:
                lv_dcm_header = f_obj
                json.dump(payload_header, lv_dcm_header, indent=4)
                
    except FileNotFoundError:
        print("\tERROR: Check if the targeted filepaths are correct.".upper())

#also if one dcm report is invalid the script mist keep running for new reports.Do that after watchdog.

def safe_archive(file_path):
    retries = 5
    while retries > 0:
        try:
            if file_path.suffix.lower() == '.txt':
                arch_reports([file_path])
            elif file_path.suffix.lower() == '.dcm':
                arch_dcm_reports([file_path])
            
            print(f"[OK] Cleaning up the source {file_path.name}")
            file_path.unlink()
            return
           
        except PermissionError:
            print(f"   [!] File {file_path.name} is busy. Retrying in 1s... ({retries} left)")
            time.sleep(1)
            retries -= 1
        except Exception as e:
            print(f"   [!] Critical error on {file_path} {type(e).__name__} - {e}")
            break
        # except Exception as e:
#             print(f"   [!] Unexpected error: {e}")
#             break

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

print("Performing scan for leftover files in the receiver directory")
leftovers = list(src_dir.glob('*'))
if not leftovers:
        print("No leftover files were found")
elif leftovers:
        for initial_file in leftovers:
            safe_archive(initial_file)


observer.start()
##start the guard shift
print("Watching the folder for new reports:")
print("-" * 20)
try:
    while True:
        time.sleep(0.5)
    # The script "sleeps" for 1 second, then loops again.
    # This uses almost zero CPU power.
except KeyboardInterrupt:
    observer.stop()

# Wait for the guard to finish packing up before closing completely.
observer.join()





    
       
          



