"""Shared rows for the hidden tests. Every row is valid under every part."""
HEADER = "record_id,business_name,tax_id,country,incorporation_date,owner_name,owner_email"
US = "m-1,Blue Bottle Roasters,12-3456789,US,2014-03-09,Dana Park,dana@bluebottle.example"
GB = "m-2,Northwind Traders,09887766,GB,2018-06-01,Sam Ortiz,sam@northwind.example"
CA = "m-3,Maple Leaf Outfitters,123456789,CA,2020-02-29,Ana Silva,ana@maple.example"
FR = "m-4,Cafe Lumiere,FR12345678,FR,2016-09-12,Claire Dubois,claire@lumiere.example"


def codes(result):
    return sorted((e.code, e.field) for e in result.errors)


def row(record_id="m-9", name="Harbour Bikes", tax_id="45-6789012", country="US",
        date="2012-04-23", owner="Tom Reid", email="tom@harbour.example"):
    return ",".join([record_id, name, tax_id, country, date, owner, email])
