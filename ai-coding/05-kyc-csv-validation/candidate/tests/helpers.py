HEADER = "record_id,business_name,tax_id,country,incorporation_date,owner_name,owner_email"
ROW_1 = "m-1,Blue Bottle Roasters,12-3456789,US,2014-03-09,Dana Park,dana@bluebottle.example"
ROW_2 = "m-2,Northwind Traders,09887766,GB,2018-06-01,Sam Ortiz,sam@northwind.example"


def codes(result):
    return sorted((e.code, e.field) for e in result.errors)
