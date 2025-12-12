import csv

new_rows = [
    ['PASL','PA to Self','', 'FALSE','TRUE','TRUE'], 
    ['PASP','PA to Spouse','', 'FALSE','TRUE','TRUE'],
    ['VLIT','Valuable Items','', 'FALSE','TRUE','TRUE'], 
    ['ALAC','Alternate Accommodation','', 'FALSE','TRUE','TRUE']
]

with open('data/add_on_master.csv', 'a', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerows(new_rows)
print("Appended rows.")
