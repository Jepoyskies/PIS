import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xjhs_pis.settings')
django.setup()

from core.models import Offense

# Format: (Type, Code, Name, Demerits, Sanction, Count, Classification)
OFFENSES_DATA = [
    # PAGE 1
    ("Conduct", "NCP", "NCP", 5, "", 0.0, "Minor"),
    ("Conduct", "LUEOC", "(Lunch)Unauthorized entry of classroom", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "1VWW", "1st Warning-Vulgarity of Words", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "A-PR", "Absent - X-PREP", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "AM1", "Absent 1st period", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "AM2", "Absent 2nd period", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "AM3", "Absent 3rd period", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "AM4", "Absent 4th period", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "PM5", "Absent 5th period", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "PM6", "Absent 6th period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Absence", "PM7", "Absent 7th period", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "PM8", "Absent 8th period", 5, "1 Hr CS", 0.5, "Minor"),
    ("Absence", "AMC", "Absent-Club Hour", 5, "1 Hr CS", 1.0, "Minor"),
    ("Absence", "AWA", "Absent-Whole Afternoon", 5, "1 Hr CS", 1.0, "Minor"),
    ("Absence", "WD", "Absent-Whole Day", 5, "1 Hr CS", 1.0, "Minor"),
    ("Absence", "AWM", "Absent-Whole Morning", 5, "3 Hrs CS", 1.0, "Minor"),
    ("Absence", "AOI", "Allowing Another To Use ID", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "AOTCP", "Allowing Other To Use Cellphone During Class Hour", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "AFEL", "Assisted in making falsified Excuse Letter", 10, "3 Hr CS", 1.0, "Major"),
    ("Conduct", "BP", "Body Piercing", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "B", "Boxing A Classmate/School Mate", 50, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "BGw/oP", "Bringing Gadget/s Without Permission", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "BDW", "Bringing Of Deadly Weapon", 50, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "BFS", "Bringing of Fidget Spinner to school", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "BOSSF", "Bringing of Softdrinks/Junkfood", 50, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "BPM", "Bringing Pornographic Magazine", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "LRC", "Brought Out Reserve Book from the LRC", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "BU", "Bullying (Physical, Verbal, Cyber)", 50, "1 Hr CS", 1.0, "Major"),
    ("Absence", "CL", "Campus Leave without permission", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CARE", "Carelessness Resulting to Offense", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "COF", "Challenging Other To Fight", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CGCIC", "Charging Gadgets / C-Phone Inside the Classroom", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "CH", "Cheating", 100, "", 1.0, "Major"),

    # PAGE 2
    ("Conduct", "CF", "Climbing Up The Fence", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CLH", "Colored hair", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CN", "Colored Nails", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "CNL", "Colored Nails / Long", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CDLR", "Continued Disregard Of LRC Rule", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CDSP", "Continued Disregard Of School Policy", 20, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "CDTW", "Continued Disregard of Teacher's Warning", 10, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "CA", "Copying Of Assignments", 20, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "ICP", "Corridor Pass Improper Use", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "CPHV", "CP Hands Off Violation", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "CRF", "Criticizing Another Resulting To A fight", 20, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "CV", "Curfew Violations", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "C", "Cursing Another", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CCC", "Cutting Classes", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC1", "Cutting Classes 1st Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC2", "Cutting Classes 2nd Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC3", "Cutting Classes 3rd Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC4", "Cutting Classes 4th Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC5", "Cutting Classes 5th Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC6", "Cutting Classes 6th Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC7", "Cutting Classes 7th Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CC8", "Cutting Classes 8th Period", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CCDH", "Cutting Classes During Club Hour", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "CCPR", "Cutting Classes during PCEER Review", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CRO", "Cyber Related Offense", 100, "", 1.0, "Major"),
    ("Conduct", "DCP", "Destroying Canteen Property", 20, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "DSP", "Destroying School Property", 50, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "DCM", "Did Not Attend Class Mass", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DACH", "Did Not Attend Club Hour", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DAI", "Did Not Attend Intramurals", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DAM", "Did Not Attend Morning Assembly", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DAO", "Did Not Attend Orientation", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DNBLG", "Did Not Bring Lab. Gown/Apron", 5, "1 Hr CS", 1.0, "Minor"),

    # PAGE 3
    ("Conduct", "DCR", "Did Not Claim Report Card", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DNC", "Did Not Clean", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "JSG", "Did Not Follow JS Guidelines", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DGCP", "Did Not Give Communications To Parents", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DSB", "Did Not Observe Silence Bell", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "CS", "Did Not Render Community Service", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DA", "Did Not Return Answer Sheet", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DBM", "Did Not Return Borrowed Materials", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DRS", "Did Not Return Reply Slip", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DRC", "Did Not Return Report Card", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DT", "Did Not Return Test Paper", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DSHC", "Did Not Submit Handbook Contract", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DPA", "Did Not Submit Project/Assignment", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DH", "Dishonesty", 100, "", 1.0, "Major"),
    ("Conduct", "DO", "Disobedience", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DL", "Disregard Of LRC Rules/Regulations", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DSRTC", "Disregard of Sch. Rules:No Internet cafe until 7PM", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DTI", "Disregard of Teacher's Instruction", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DTR", "Disregard to Rules", 20, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "D", "Disrespect", 100, "", 1.0, "Major"),
    ("Conduct", "D1STO", "Disrespect (1st Offense)", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DOS", "Disrespect Other Students", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "DC", "Disturbing The Class", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DTS", "Doing Things Not Related To The Subject", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "DLR", "Drinking Liquor", 100, "", 1.0, "Major"),
    ("Conduct", "EDC", "Eating During Class Hour", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "EIC", "Eating inside the classroom", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "ETXASC", "Eating inside XASC", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "E", "Eating/Chewing Gum Inside Classroom/Campus", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "EAC", "Entering Another Classroom", 5, "1 Hr CS", 0.0, "Minor"),

    # PAGE 4
    ("Conduct", "E1", "Entering Class W/O Admit-To-Class", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "EFCR", "Entering Female's CR", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "EOL", "Entering Off-Limits Area", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "EORDR", "Entering Other's Room During Retreat", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "ECC", "Escape from Cleaning the Classroom", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "EC", "Escape from CS", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "EXVIOL", "Exam Violation", 5, "1 Hr CS", 0.0, "Minor"),
    ("Conduct", "FE", "Falsified Excuse Letter", 50, "1 Hr CS", 1.0, "Major"),
    ("Conduct", "FID", "Falsified ID", 50, "1 Hr CS", 0.0, "Major"),
    ("Conduct", "UFN", "Fictitious Name", 30, "3 Hrs CS", 1.0, "Major"),
    ("Conduct", "F", "Fighting", 50, "2 Hrs CS", 1.0, "Major"),
    ("Conduct", "FWI", "Fighting with Injury", 100, "1 Day Suspension", 1.0, "Major"),
    ("Conduct", "FGY", "Forgery", 100, "", 1.0, "Major"),
    ("Conduct", "FTY", "Fraternity", 100, "", 1.0, "Major"),
    ("Conduct", "GP", "Gleaning at Another Paper", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "GO", "Going Out The Classroom W/O Permission", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "GLC", "Going to Lockers During Class/In between periods", 5, "1 Hr CS", 1.0, "Minor"),
    ("Conduct", "GTWP", "Got the things of others without permission", 5, "1 Hr CS", 1.0, "Minor"),
]

def run():
    print(f"Checking {len(OFFENSES_DATA)} offenses...")
    created_count = 0
    updated_count = 0
    
    for o_type, code, name, dem, sanc, cnt, cls in OFFENSES_DATA:
        obj, created = Offense.objects.update_or_create(
            code=code,
            defaults={
                'offense_type': o_type, 
                'name': name, 
                'default_demerits': dem, 
                'default_sanction': sanc, 
                'default_count': cnt, 
                'classification': cls
            }
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    print(f"✅ Seeding Complete!")
    print(f"✨ Created: {created_count}")
    print(f"🔄 Updated: {updated_count}")

if __name__ == '__main__':
    run()