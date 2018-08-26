# pagekeeper
A simple utility for collecting and analyzing the number of printed pages of network printers<br>
Collect data and compare it with the data for the 26th:
<pre>
python3 main.py -c 2018-08-26
</pre>
##Configuration
conf.json
<pre>
{
  "database": "Name of database file",
  "printers" : [
    {
      "title": "Short printer name",
      "ip" : "IP Address",
      <i>"oid" : SNMP OID key for read(optional)</i>
      "description": "Full description",
      "groups" : [ List of analyze group ]
    }
  ]
}
</pre>
##Arguments
main.py args START END<br>
<b>-c --collect</b> - Collect counts<br/>
<b>-r --refresh</b> - Refresh count, if value exist<br/>
<b>--clear</b> - Clear database<br/>
<b>--conf</b> <i>filename</i> - Use configuration file<br/>
<b>START</b> - date of loading if initial data<br/>
<b>END</b> - date of end data(if it is empty, then today)
