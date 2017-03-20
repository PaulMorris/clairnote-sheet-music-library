import csv

def merge_csv_data(old_csv, new_csv_data, id_field_name):
    """ Merge data from previous csv and mark which items are new.
        old_csv (string) is the path to the previous csv file
        new_csv_data (list) data destined for the new csv file
        id_field_name (string) key for the id value for items in new_csv_data
        returns (list) merged data """

    # get old meta data
    old_meta_data = {}

    with open(old_csv, newline='') as old_csv_read:
        reader = csv.DictReader(old_csv_read)
        for row in reader:
            item_id = int(row[id_field_name])

            if row['new?'] == 'T':
                print('\nOOPS! - There is an item marked as NEW in the OLD csv file... ID: ' + str(item_id))

            old_meta_data[item_id] = {
                'omit?': row['omit?'],
                'omit-reason': row['omit-reason'],
                'new?': row['new?'],
                'error-status?': row['error-status?']
            }

    # merge old meta data into new data and mark new items as new
    # the meta data fields should be empty in the new data, so nothing is overwritten
    old_total = len(old_meta_data)
    new_total = len(new_csv_data)
    merged_csv_data = []

    for item in new_csv_data:
        # note: item is a dict so it is appended by reference not by value
        merged_csv_data.append(item)
        item_id = int(item[id_field_name])

        if item_id in old_meta_data:
            merged_csv_data[-1].update(old_meta_data[item_id])
            # remove the item from old_meta_data so we can identify any orphaned works
            del old_meta_data[item_id]
        else:
            merged_csv_data[-1]['new'] = 'T'

    print('\n' + str(old_total), 'Works in previous CSV file.')
    print(new_total, 'Works in current CSV file.')
    print(str(new_total - old_total), 'Total new works.\n')

    if len(old_meta_data) > 0:
        print("Orphaned works that were in previous CSV file but were not in current CSV file:", sorted(old_meta_data.keys()))
    else:
        print("There were no orphaned works, all items in previous CSV are in current CSV.")

    return merged_csv_data
