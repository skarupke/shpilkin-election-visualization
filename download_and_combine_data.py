import urllib.request
import csv
import os
import xlrd

file_folder = 'census_estimates/'

def file_name_csv(i):
    file = "co-est00int-01-"
    if i < 10:
        file = file + '0'
    return file + str(i) + ".csv"
def file_name_xlsx(i):
    file = "co-est2019-annres-"
    if i < 10:
        file = file + '0'
    return file + str(i) + ".xlsx"

def download_population_estimates():

    def download_with_pattern(folder, file_name):
        for i in range(1, 57):
            file = file_name(i)
            print("Downloading " + folder + file)
            try:
                urllib.request.urlretrieve(folder + file, file_folder + file)
            except:
                pass

    folder = "https://www2.census.gov/programs-surveys/popest/tables/2000-2010/intercensal/county/"
    download_with_pattern(folder, file_name_csv)

    folder = "https://www2.census.gov/programs-surveys/popest/tables/2010-2019/counties/totals/"
    download_with_pattern(folder, file_name_xlsx)



#download_population_estimates()


def combine_into_one_table():
    by_state = {}
    state_name = {}
    for i in range(1, 57):
        path = file_folder + file_name_csv(i)
        if not os.path.exists(path):
            continue
        print(path)
        with open(path) as f:
            reader = csv.reader(f)
            csv_rows = [row for row in reader]

        path = file_folder + file_name_xlsx(i)
        print(path)
        book = xlrd.open_workbook(path)
        sheet = book.sheet_by_index(0)

        def extract_from_csv(csv_rows):
            state_line = csv_rows[4]
            county_lines = csv_rows[5:]
            state = state_line[0]

            by_county = {}
            for county_line in county_lines:
                county = county_line[0]
                if not county.startswith('.'):
                    break
                county = county[1:]
                population = [int(x.replace(',', '')) for x in county_line[2:12]]
                population = { 2000 + i : population[i] for i in range(10) }
                by_county[county] = population
            return state, by_county

        def extract_from_xlsx(sheet):
            state = sheet.cell(4, 0).value.strip()
            by_county = {}
            for i in range(5, sheet.nrows):
                county = sheet.cell(i, 0).value.strip()
                if county.startswith('Note: '):
                    break
                by_year = {}
                for y in range(10):
                    pop = sheet.cell(i, y + 3).value
                    pop = int(pop)
                    by_year[2010 + y] = pop
                assert(county.endswith(state))
                county = county[:-len(state)].strip()
                assert(county.endswith(','))
                county = county[:-1].strip()
                assert(county.startswith('.'))
                county = county[1:].strip()
                by_county[county] = by_year
            return state, by_county

        state, by_county = extract_from_csv(csv_rows)
        state2, by_county2 = extract_from_xlsx(sheet)
        assert(state == state2)
        for county, by_year in by_county2.items():
            if county not in by_county:
                if county == "Petersburg Borough":
                    by_county["Petersburg Borough"] = by_county["Petersburg Census Area"]
                    del by_county["Petersburg Census Area"]
                elif county == "LaSalle Parish":
                    county = "La Salle Parish"
            if county in by_county:
                for year, pop in by_year.items():
                    by_county[county][year] = pop
            else:
                print(county)
                by_county[county] = by_year
        by_state[state] = by_county
        state_name[i] = state
        #print(state, by_county)
    return by_state, state_name

by_state, state_name = combine_into_one_table()

def zero_to_sixteen():
    by_year = {}
    # you'll have to manually download this file from
    # https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ
    with open('countypres_2000-2016.csv') as f:
        reader = csv.reader(f)
        rows = [row for row in reader]
    rows = rows[1:]
    for year in range(2000, 2020, 4):
        by_year[year] = {}
    for row in rows:
        year = int(row[0])
        state = row[1]
        if state == 'Alaska':
             # Sadly Alaska is organized differently between the two
             # files and I don't know how to match the right population
             # number to the voting results.
            continue
        county = row[3]
        if row[4] == 'NA':
            continue
        fips_code = int(row[4])
        population = by_state[state]
        def get_population(county):
            if county not in population:
                if county.startswith('Saint '):
                    county = county.replace('Saint ', 'St. ')
                #if county.startswith('Sainte '):
                #    county = county.replace('Sainte ', 'Ste. ')
                if county == 'Desoto':
                    county = 'DeSoto'
                if county == 'Dewitt':
                    county = 'DeWitt'
                if county == 'Lac Qui Parle':
                    county = 'Lac qui Parle'
                if county == 'Kansas City':
                    return population['Jackson County'], county
                def virginia_city(name, county_fips, city_fips):
                    if county != name:
                        return ''
                    elif fips_code == county_fips:
                        return name + ' County'
                    elif fips_code == city_fips:
                        return name + ' city'
                    else:
                        return ''
                va = virginia_city('Bedford', 51019, 51515)
                if va:
                    return population[va], va
                va = virginia_city('Fairfax', 51059, 51600)
                if va:
                    return population[va], va
                va = virginia_city('Franklin', 51067, 51620)
                if va:
                    return population[va], va
                va = virginia_city('Richmond', 51159, 51760)
                if va:
                    return population[va], va
                va = virginia_city('Roanoke', 51161, 51770)
                if va:
                    return population[va], va
                with_county = county + ' County'
                if with_county in population:
                    return population[with_county], with_county
                with_parish = county + ' Parish'
                if with_parish in population:
                    return population[with_parish], with_parish
                if county.endswith(' City'):
                    county = county.replace(' City', ' city')
                with_city = county + ' city'
                if with_city in population:
                    return population[with_city], with_city
            if county not in population:
                print(sorted(population.keys()))
                print(county, fips_code)
            return population[county], county
        pop_by_year, county = get_population(county)
        result_by_state = by_year[year]
        if state not in result_by_state:
            result_by_state[state] = {}
        by_county = result_by_state[state]
        if county not in by_county:
            if year not in pop_by_year:
                continue
            by_county[county] = [pop_by_year[year], int(row[9])]
        party = row[7]
        if row[8] == 'NA':
            num_votes = 0
        else:
            num_votes = int(row[8])
        if party == 'democrat':
            if len(by_county[county]) != 2:
                print(county, ", ", state, by_county[county])
            assert(len(by_county[county]) == 2)
            by_county[county].append(num_votes)
        elif party == 'republican':
            if len(by_county[county]) != 3:
                print(county, by_county[county])
            assert(len(by_county[county]) == 3)
            by_county[county].append(num_votes)
        else:
            if len(by_county[county]) == 4:
                by_county[county].append(num_votes)
            else:
                by_county[county][-1] += num_votes
    return by_year

by_year = zero_to_sixteen()

for year, by_state in by_year.items():
    with open('results_' + str(year) + '.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['County', 'State', 'Population', 'Total Votes', 'Democrats', 'Republican', 'Other'])
        for state, by_county in by_state.items():
            for county, res in by_county.items():
                writer.writerow([county, state] + res)

