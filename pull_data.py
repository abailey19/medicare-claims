import json
import requests
import csv
import pandas as pd

# For this code, update this token online using a sample application flow for now (must be registered with Blue Button)
# A collaborator has recently written code for us to get this token automatically
token = 'Z5EgFZrzf7zr1HpQGlMgu63Vre3XLn'
blue_button_url_base = 'https://sandbox.bluebutton.cms.gov'
patient_extension = '/v1/fhir/Patient/20140000008325'
eob_extension = '/v1/fhir/ExplanationOfBenefit/?patient=20140000008325'
coverage_extension = '/v1/fhir/Coverage/?beneficiary=20140000008325'
headers = {'Authorization': 'Bearer ' + token}

# Using the url provided in "Try the API" on Blue Button docs: gets the Patient Profile
patient_response = requests.get(blue_button_url_base + patient_extension, headers=headers)
# patient_data is patient_response but in formatted JSON
patient_data = patient_response.json()
# Write the data to a JSON file showing the Patient Profile
with open('patient_data.json', 'w') as outfile:
    json.dump(patient_data, outfile, indent=4)

# Get the Explanation of Benefit form, which has all the claims data
# For this sample patient: 25 carrier claims, 2 inpatient claims, 5 Part D events
eob_response = requests.get(blue_button_url_base + eob_extension, headers=headers)
eob_data = eob_response.json()
# Write the data to a JSON file
with open('eob_data.json', 'w') as outfile:
    json.dump(eob_data, outfile, indent=4)

# Not using data from this at the moment
# Get the Coverage form (mainly to see the cost, since it's pretty spread out over the EoB form)
coverage_response = requests.get(blue_button_url_base + coverage_extension, headers=headers)
coverage_data = coverage_response.json()
# Write the data to a JSON file
with open('coverage_data.json', 'w') as outfile:
    json.dump(coverage_data, outfile, indent=4)


######################################
# Parsing the data in the the patient and eob json files.
# Writing it to a parsed data file for easily-readable text.
#####################################
parsed_data_file = open('parsed_data.txt', 'w')
# Write patient info
parsed_data_file.write("Patient ID: " + patient_data["id"] + "\n")
parsed_data_file.write("Patient name: " + patient_data["name"][0]["family"] + ", "
                       + patient_data["name"][0]["given"][0] + " "
                       + patient_data["name"][0]["given"][1] + "\n")
parsed_data_file.write("Patient gender: " + patient_data["gender"] + "\n")
parsed_data_file.write("Patient birth date: " + patient_data["birthDate"] + "\n")
parsed_data_file.write("Patient race: " + patient_data["extension"][0]["valueCoding"]["display"] + "\n")
parsed_data_file.write("Patient address: " + "District code " + patient_data["address"][0]["district"]
                       + ", State code " + patient_data["address"][0]["state"]
                       + ", Postal code " + patient_data["address"][0]["postalCode"] + "\n")
parsed_data_file.write('\n')

# Parse and write eob form data
# Initialize the list of lists eob_csv_data with column headers,
# and add an array of data for each claim to it to eventually put it into a csv file and then a pandas dataframe
eob_csv_data = [["Claim Number", "Claim ID", "Patient ID", "Claim Type Code", "Type of Claim", "EOB type",
                 "Claim Record Type Code", "Type of Claim Record", "Service Start Date", "Service End Date",
                 "Procedure 1 Code", "Procedure 1 Type", "Service 1 Code", "Service 1 Type",
                 "Procedure 2 Code", "Procedure 2 Type", "Service 2 Code", "Service 2 Type",
                 "Procedure 3 Code", "Procedure 3 Type", "Service 3 Code", "Service 3 Type",
                 "Procedure 4 Code", "Procedure 4 Type", "Service 4 Code", "Service 4 Type",
                 "Procedure 5 Code", "Procedure 5 Type", "Service 5 Code", "Service 5 Type",
                 "Procedure 6 Code", "Procedure 6 Type", "Service 6 Code", "Service 6 Type",
                 "Provider 1 Type Code", "Provider 1 Type", "Provider 2 Type Code", "Provider 2 Type",
                 "Provider 3 Type Code", "Provider 3 Type", "Provider 4 Type Code", "Provider 4 Type",
                 "Provider 5 Type Code", "Provider 5 Type", "Provider 6 Type Code", "Provider 6 Type",
                 "Main Provider ID", "Provider Role Code", "Provider Role", "Provider Qualification",
                 "Place of Service 1 Code", "Place of Service 1", "State 1 Code", "State 1", "ZIP Code 1", "Locality Code 1",
                 "Place of Service 2 Code", "Place of Service 2", "State 2 Code", "State 2", "ZIP Code 2", "Locality Code 2",
                 "Place of Service 3 Code", "Place of Service 3", "State 3 Code", "State 3", "ZIP Code 3", "Locality Code 3",
                 "Place of Service 4 Code", "Place of Service 4", "State 4 Code", "State 4", "ZIP Code 4", "Locality Code 4",
                 "Place of Service 5 Code", "Place of Service 5", "State 5 Code", "State 5", "ZIP Code 5", "Locality Code 5",
                 "Place of Service 6 Code", "Place of Service 6", "State 6 Code", "State 6", "ZIP Code 6", "Locality Code 6",
                 "Submitted Charges 1", "Allowed Charges 1", "Submitted Charges 2", "Allowed Charges 2",
                 "Submitted Charges 3", "Allowed Charges 3", "Submitted Charges 4", "Allowed Charges 4",
                 "Submitted Charges 5", "Allowed Charges 5", "Submitted Charges 6", "Allowed Charges 6",
                 "Total Submitted Charges", "Total Allowed Charges",
                 "Diagnosis 1 Code", "Diagnosis 1", "Diagnosis 2 Code", "Diagnosis 2", "Diagnosis 3 Code",
                 "Diagnosis 3", "Diagnosis 4 Code", "Diagnosis 4", "Diagnosis 5 Code", "Diagnosis 5"]]

claim_number = 1

# Variables to count the percentage of times in all the claims that these fields are empty
item_2_empty = 0
item_3_empty = 0
item_4_empty = 0
item_5_empty = 0
item_6_empty = 0
diagnosis_2_empty = 0
diagnosis_3_empty = 0
diagnosis_4_empty = 0
diagnosis_5_empty = 0

# Loop through each claim in the EOB file
for resource in eob_data["entry"]:

    empty_items = 0
    empty_diagnoses = 0

    resource_csv_data = [claim_number] # The data for this claim

    # Parse care team data
    care_team_data = resource["resource"]["careTeam"][0]  # dict

    # Parse diagnosis data
    diagnosis_data = resource["resource"]["diagnosis"]  # list

    # For procedure/service, treatment, service period, and location data (all within the 'item' object):
    item_data = resource["resource"]["item"]  # list


    # Write data to parsed data file for easier reading,
    # and add it to csv data to put it into a pandas dataframe:

    # Write the claim number
    parsed_data_file.write("CLAIM " + str(claim_number) + ": \n")

    # Write and add the claim ID
    claim_id = resource["resource"]["id"]
    parsed_data_file.write("Claim ID: " + claim_id + '\n')
    resource_csv_data.append(claim_id)

    # Write and add the patient ID
    patient_id = resource["resource"]["patient"]["reference"][8:]
    parsed_data_file.write("Patient ID: " + patient_id + '\n')
    resource_csv_data.append(patient_id)

    # Write and add the EOB and claim type
    claim_type_code = resource["resource"]["type"]["coding"][0]["code"]
    claim_type_display = resource["resource"]["type"]["coding"][0]["display"]
    eob_type = resource["resource"]["type"]["coding"][1]["code"]
    claim_record_type_code = resource["resource"]["type"]["coding"][3]["code"]
    claim_record_type_display = resource["resource"]["type"]["coding"][3]["display"]
    parsed_data_file.write("Claim Type: \n" + "\tCode: " + claim_type_code + '\n'
                           + "\tDisplay: " + claim_type_display + '\n' + "\tEOB type: " + eob_type + " \n"
                           + "\tRecord Code: " + claim_record_type_code + '\n'
                           + "\tRecord Display: " + claim_record_type_display + '\n')
    resource_csv_data.append(claim_type_code)
    resource_csv_data.append(claim_type_display)
    resource_csv_data.append(eob_type)
    resource_csv_data.append(claim_record_type_code)
    resource_csv_data.append(claim_record_type_display)

    # Write and add the service start and end dates
    # (If there was a part A claim, I would use those dates as the overall start and end dates).
    # Since there is not, I've used the dates from the first part B claim just as a filler for now.
    start_date = item_data[0]["servicedPeriod"]["start"]
    end_date = item_data[0]["servicedPeriod"]["end"]
    parsed_data_file.write("Service period: \n" + "\t Start date: " + start_date + '\n'
                           + "\t End date: " + end_date + '\n')
    resource_csv_data.append(start_date)
    resource_csv_data.append(end_date)
    parsed_data_file.write('\n')

    # Add the treatment and service data (function) to the csv data
    item_number = 1
    # Loop through all the items in the claim (each of which has treatment/service info)
    for section in item_data:
        # Write procedure data
        resource_csv_data.append(section["extension"][2]["valueCoding"]["code"])
        resource_csv_data.append(section["extension"][2]["valueCoding"]["display"])

        # Write treatment data
        treatment_data_category = section["category"]["coding"][0]
        resource_csv_data.append(treatment_data_category["code"])
        resource_csv_data.append(treatment_data_category["display"])

        item_number += 1
    for i in range(6 - item_number + 1):
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        empty_items += 1
    # Keeping track of when items are empty
    if empty_items > 1:
        item_6_empty += 1
    if empty_items > 2:
        item_5_empty += 1
    if empty_items > 3:
        item_4_empty += 1
    if empty_items > 4:
        item_3_empty += 1
    if empty_items > 5:
        item_2_empty += 1

    # Form: care team data and location/facility

    # Write care team data to parsed data file and add it to the csv data
    parsed_data_file.write("Care Team: \n")
    provider_number = 1
    # Loop through each element in the care team data
    for key in care_team_data:
        if key == "extension":
            parsed_data_file.write("Providers: \n")
            count = 0
            for element in care_team_data[key]:
                if element["url"] == "https://bluebutton.cms.gov/resources/variables/carr_line_prvdr_type_cd":
                    code = element["valueCoding"]["code"]
                    if code == '0':
                        message = "Clinics, groups, associations, partnerships, or other entities"
                    elif code == '1':
                        message = "Physicians or suppliers reporting as solo practitioners"
                    elif code == '2':
                        message = "Suppliers (other than sole proprietorship)"
                    elif code == '3':
                        message = "Institutional provider"
                    elif code == '4':
                        message = "Independent laboratories"
                    elif code == '5':
                        message = "Clinics (multiple specialties)"
                    elif code == '6':
                        message = "Groups (single specialty)"
                    elif code == '7':
                        message = "Other entities"
                    else:
                        message = ""
                    parsed_data_file.write("\t Code: " + code + '\n')
                    parsed_data_file.write("\t " + message + '\n')
                    resource_csv_data.append(code)
                    resource_csv_data.append(message)
                    count += 1
            for i in range(6-count):
                resource_csv_data.append("empty") # Change to something else (maybe 999 or NaN or blank)
                resource_csv_data.append("empty") # Change to something else (maybe 999 or NaN or blank)
        elif key == "provider":
            parsed_data_file.write("Provider " + str(provider_number) + ": \n")
            provider_number += 1
            parsed_data_file.write("\t Provider identifier: " + care_team_data["provider"]["identifier"]["value"] + '\n')
            resource_csv_data.append(care_team_data["provider"]["identifier"]["value"])
        elif key == "role":
            parsed_data_file.write("\t Provider role: \n\t\tCode: " + care_team_data["role"]["coding"][0]["code"]
                                   + "\n\t\tDisplay: " + care_team_data["role"]["coding"][0]["display"] + '\n')
            resource_csv_data.append(care_team_data["role"]["coding"][0]["code"])
            resource_csv_data.append(care_team_data["role"]["coding"][0]["display"])
        elif key == "qualification":
            parsed_data_file.write(
                "\t Provider qualification code: " + care_team_data["qualification"]["coding"][0]["code"] + '\n')
            resource_csv_data.append(care_team_data["qualification"]["coding"][0]["code"])
    parsed_data_file.write('\n')

    # Add the location data to the csv data
    item_number = 1
    # Loop through all the items in the claim (each of which has location info)
    for section in item_data:
        # Location data
        location_data_1 = section["locationCodeableConcept"]["extension"]  # list
        location_data_2 = section["locationCodeableConcept"]["coding"][0]  # dict
        # Place of Service
        resource_csv_data.append(location_data_2["code"])
        resource_csv_data.append(location_data_2["display"])
        for element in location_data_1:
            # State
            if element["url"] == "https://bluebutton.cms.gov/resources/variables/prvdr_state_cd":
                resource_csv_data.append(element["valueCoding"]["code"])
                resource_csv_data.append(element["valueCoding"]["display"])
            # ZIP code
            elif element["url"] == "https://bluebutton.cms.gov/resources/variables/prvdr_zip":
                resource_csv_data.append(element["valueCoding"]["code"])
            # Locality
            elif element["url"] == "https://bluebutton.cms.gov/resources/variables/carr_line_prcng_lclty_cd":
                resource_csv_data.append(element["valueCoding"]["code"])

        item_number += 1
    for i in range(6 - item_number + 1):
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)

    # Add the cost information to the csv data
    item_number = 1
    # Loop through all the items in the claim (each of which has location info)
    for section in item_data:
        # Charges data for each item
        submitted_charges_data = section["adjudication"][7]["amount"]
        allowed_charges_data = section["adjudication"][8]["amount"]
        resource_csv_data.append(str(submitted_charges_data["value"]) + " " + submitted_charges_data["code"])
        resource_csv_data.append(str(allowed_charges_data["value"]) + " " + allowed_charges_data["code"])

        item_number += 1
    for i in range(6 - item_number + 1):
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)
        resource_csv_data.append("empty")  # Change to something else (maybe 999 or NaN or blank)

    # Total charges for the claim
    total_submitted_charges = resource["resource"]["extension"][8]["valueMoney"]
    total_allowed_charges = resource["resource"]["extension"][9]["valueMoney"]
    resource_csv_data.append(str(total_submitted_charges["value"]) + " " + total_submitted_charges["code"])
    resource_csv_data.append(str(total_allowed_charges["value"]) + " " + total_allowed_charges["code"])

    # Write diagnosis data and add it to the csv data
    parsed_data_file.write("Diagnoses:" + "\n")
    diagnosis_number = 0
    for key in diagnosis_data:  # each "sequence" is a dict
        diagnosis_info = key["diagnosisCodeableConcept"]["coding"][0]  # this is a dict
        parsed_data_file.write("Diagnosis " + str(diagnosis_number))
        if "type" in key and key["type"][0]["coding"][0]["code"] == "principal":
            parsed_data_file.write(" (principal diagnosis)")
        parsed_data_file.write(": \n")
        if "code" in diagnosis_info:
            parsed_data_file.write("\t Code: " + diagnosis_info["code"] + '\n')
            resource_csv_data.append(diagnosis_info["code"])
        else:
            resource_csv_data.append("empty")
        if "display" in diagnosis_info:
            parsed_data_file.write("\t Display: " + diagnosis_info["display"] + '\n')
            if "type" in key and key["type"][0]["coding"][0]["code"] == "principal":
                resource_csv_data.append(diagnosis_info["display"] + " (principal diagnosis)")
            else:
                resource_csv_data.append(diagnosis_info["display"])
        else:
            resource_csv_data.append("empty")
        diagnosis_number += 1
    for i in range(5 - diagnosis_number + 1):
        resource_csv_data.append("empty")
        resource_csv_data.append("empty")
        empty_diagnoses += 1
    # Keep track of when there are fewer diagnoses and the other fields are empty
    if empty_diagnoses > 1:
        diagnosis_5_empty += 1
    if empty_diagnoses > 2:
        diagnosis_4_empty += 1
    if empty_diagnoses > 3:
        diagnosis_3_empty += 1
    if empty_diagnoses > 4:
        diagnosis_2_empty += 1

    # Write procedure, treatment, service period, and location data for each item to the parsed data file
    item_number = 1
    for section in item_data:
        parsed_data_file.write("Item " + str(item_number) + ": \n")
        # Write procedure data
        parsed_data_file.write("Procedure: \n")
        parsed_data_file.write("\t Code: " + section["extension"][2]["valueCoding"]["code"] + "\n")
        parsed_data_file.write("\t Display: " + section["extension"][2]["valueCoding"]["display"] + "\n")
        parsed_data_file.write('\n')

        # Write treatment data
        parsed_data_file.write("Treatment: \n")
        treatment_data_category = section["category"]["coding"][0]
        parsed_data_file.write("Type of service: \n" + "\t Code: " + treatment_data_category["code"] + '\n'
                               + "\t Display: " + treatment_data_category["display"] + '\n')
        treatment_data_service = section["service"]["coding"][0]
        parsed_data_file.write("Service: \n" + "\t Version: " + treatment_data_service["version"] + '\n'
                               + "\t Code: " + treatment_data_service["code"] + '\n')
        parsed_data_file.write('\n')

        # Write service period
        parsed_data_file.write("Service period: \n" + "\t Start date: " + section["servicedPeriod"]["start"] + '\n'
                               + "\t End date: " + section["servicedPeriod"]["end"] + '\n')
        parsed_data_file.write('\n')

        # Write location data
        parsed_data_file.write("Location: \n")
        location_data_1 = section["locationCodeableConcept"]["extension"]  # list
        location_data_2 = section["locationCodeableConcept"]["coding"][0]  # dict
        for element in location_data_1:
            if element["url"] == "https://bluebutton.cms.gov/resources/variables/prvdr_state_cd":
                parsed_data_file.write("State: \n" + "\t Code: " + element["valueCoding"]["code"] + '\n'
                                       + "\t Display: " + element["valueCoding"]["display"] + '\n')
            elif element["url"] == "https://bluebutton.cms.gov/resources/variables/prvdr_zip":
                parsed_data_file.write("ZIP Code: \n" + "\t Code: " + element["valueCoding"]["code"] + '\n')
            elif element["url"] == "https://bluebutton.cms.gov/resources/variables/carr_line_prcng_lclty_cd":
                parsed_data_file.write("Locality: \n" + "\t Code: " + element["valueCoding"]["code"] + '\n')
        parsed_data_file.write("Place of Service (type of facility): \n" + "\t Code: " + location_data_2["code"] + '\n'
                               + "\t Display: " + location_data_2["display"] + '\n')

        # Write the cost information
        parsed_data_file.write("Cost Information: \n")
        submitted_charges_data = section["adjudication"][7]["amount"]
        allowed_charges_data = section["adjudication"][8]["amount"]
        parsed_data_file.write("\t Submitted Charges: " + str(submitted_charges_data["value"]) + " " + submitted_charges_data["code"])
        parsed_data_file.write("\t Allowed Charges: " + str(allowed_charges_data["value"]) + " " + allowed_charges_data["code"])

        parsed_data_file.write('\n')
        item_number += 1

    claim_number += 1
    eob_csv_data.append(resource_csv_data)
    parsed_data_file.write('\n\n')

parsed_data_file.close()

print("Item 2 empty " + str(item_2_empty/(claim_number-1)*100) + "% of the time")
print("Item 3 empty " + str(item_3_empty/(claim_number-1)*100) + "% of the time")
print("Item 4 empty " + str(item_4_empty/(claim_number-1)*100) + "% of the time")
print("Item 5 empty " + str(item_5_empty/(claim_number-1)*100) + "% of the time")
print("Item 6 empty " + str(item_6_empty/(claim_number-1)*100) + "% of the time")
print("Diagnosis 2 empty " + str(diagnosis_2_empty/(claim_number-1)*100) + "% of the time")
print("Diagnosis 3 empty " + str(diagnosis_3_empty/(claim_number-1)*100) + "% of the time")
print("Diagnosis 4 empty " + str(diagnosis_4_empty/(claim_number-1)*100) + "% of the time")
print("Diagnosis 5 empty " + str(diagnosis_5_empty/(claim_number-1)*100) + "% of the time")
print()

######################################
# Put parsed data in a CSV file
######################################
patient_csv_data = [["ID", "Last Name", "First Name", "Middle Name", "Gender", "Birth Date", "Race", "Address District",
                     "Address State", "Address Zip Code"],
                    [patient_data["id"], patient_data["name"][0]["family"], patient_data["name"][0]["given"][0],
                     patient_data["name"][0]["given"][1], patient_data["gender"], patient_data["birthDate"],
                     patient_data["extension"][0]["valueCoding"]["display"], patient_data["address"][0]["district"],
                     patient_data["address"][0]["state"], patient_data["address"][0]["postalCode"]]]

with open('patient.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerows(patient_csv_data)

csvFile.close()

with open('eob.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerows(eob_csv_data)

csvFile.close()

######################################
# Load CSV data into pandas
######################################
patient_table_data = pd.read_csv("patient.csv")
eob_table_data = pd.read_csv("eob.csv")

writer = pd.ExcelWriter('claims.xlsx')
patient_table_data.to_excel(writer, 'Patient Data')
eob_table_data.to_excel(writer, 'EOB Data')
writer.save()

# Printing to test - the content is more easily readable in the excel file
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(patient_table_data)
print()
print()
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(eob_table_data)
