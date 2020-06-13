# Processing Medicare claims

## The Project
I have been participating in a WISP research internship with Dr. Inas Khayal at DHMC.
I have worked to learn the structure of a Medicare claim and write code to pull and organize relevant data from a claim. This code will serve as the back end for a web app to allow patients and doctors to access their data.

## The Code
My code parses data from patient data files, which contain basic information about patients, and from explanation of benefit files, which contain multiple Medicare claims. So far, it extracts data that Dr. Khayal and I have deemed relevant, such as treatment, diagnosis, providers, location, and cost. It puts this data into a Pandas dataframe, which I am currently writing to an Excel file for easy readability.
