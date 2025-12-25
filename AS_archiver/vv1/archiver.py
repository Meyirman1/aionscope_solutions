#Building first folders so when it return none it doesn't nulify the address.
##AUTOMATING dest_paths with pathlib
##                    THE GLOSSARY FOR SHORTED WORDS:
## fp (filepath).
## lv (local view)

import json
from pathlib import Path 


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

def extract_metadata(patient_id,date,patient_fname,patient_lname,modality):
    extract  = {
        "patient_id": f"P{patient_id}",
        "date": f"{date}",
        "patient_firstname": f"{patient_fname}",
        "patient_lastname": f"{patient_lname}",
        "modality": f"{modality}"
                 }
    return extract

def archiving_report(orig_reports):
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
            print(f"\nThe report with ID:{parts[1]} was archived successfully!")
                    
            with open(dest_meta_fp, 'w') as json_ouput:
                json_dest = json_ouput
                json.dump(payload_metadata, json_dest, indent=4)
            with open(lv_dest_meta_fp, 'w') as lv_json_output:
                lv_json_dest = lv_json_output
                json.dump(payload_metadata,lv_json_dest, indent=4)
    except FileNotFoundError:
        print("\tERROR: Check if the targeted filepaths are correct.".upper())
    
archiving_report(src_reports)