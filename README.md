# bp2.py

This is the second attempt at making an automatic building permit processor.

# Use (currently working)

1. Download the permit data from [here](http://cpdbprod/ReportServer/Pages/ReportViewer.aspx?%2fLand%2fStatistics%2fNew+Construction+Report&rs:Command=Render) and save to `/data/<year>` as `city_<year>.xlsx`  
2. Open the command line in the bp2 directory  
3. Enter `python bp2.py get_data --replace` to update data from SDE (This takes ~30 min)  
4. Enter `python bp2.py process_city <year>` to process the downloaded Excel file  
5. Profit  

## Features to come

* Output tables: `permits` (n features/parcel) and `new_units` (1 feature/parcel; allows for density)  
* Installation using `setup.py`  
* a `process_county` option  
* export to .json and .shp
* a `report` option to generate reports using HTML templates and graphs  

# Rules
Building permits must have >0 unit(s)  
BNCON is an "other" building type that may/may not include new units 
BAARC is a "remodel" building type that may/may not include new units