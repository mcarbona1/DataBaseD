#!/usr/bin/env python3

import sys
from datetime import datetime
from collections import defaultdict
import pprint
sys.path.append('..')
from distributorScraper import sqlFunctions

COLORS = {'Steam': '#B8E714',
          'GOG': '#AB34AF',
          'Epic Games': '#0074E4'}

# Instructions for the codermen:
  # pass in game_id to get js script to plot prices
  # place outputted js script in headder of page
  # to display plot, use a div (<div id="curve_chart" style="width: 900px; height: 500px"></div>)
def get_price_history(game_id: int):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"select curr_price, date, source from MSRP m inner join PRICES p on m.MSRP_ID = p.MSRP_ID where game_id = {game_id} order by date, source;")
    history = defaultdict(dict)
    sources = set()

    maxPrice = 0
    for item in cursor.fetchall():
        maxPrice = max(maxPrice, item[0])
        history[f"new Date({item[1].year}, {item[1].month - 1}, {item[1].day})"][item[2]] = item[0]
        sources.add(item[2])
    
    if not sources:
        return None

    data = [['date'] + [source for source in sources]] + [[date] + [history[date].get(source, "null") for source in sources] for date in history]
    data = pprint.pformat(data).replace("'null'", "null").replace("'new Date", "new Date").replace(")'", ")")

    colors = pprint.pformat([COLORS[source] for source in sources])

    script = f"""<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
    google.charts.load('current', {{'packages':['corechart']}});
    google.charts.setOnLoadCallback(drawChart);
    function drawChart() {{
        var data = google.visualization.arrayToDataTable({data});
    
    var options = {{
          curveType: 'none',
          chartArea: {{ width: '90%', height: '85%' }},
          legend: {{ 
            position: 'in',
            textStyle: {{ color: '#FFFFFF' }}
          }},
          backgroundColor: '#000000',
          hAxis: {{ 
            format: 'M/d/yy',
            textStyle: {{ color: '#FFFFFF' }},
            gridlines: {{
                color: 'transparent'
            }}
        }},
          vAxis: {{
            format: '$#,###',
            textStyle: {{ color: '#FFFFFF' }},
            minValue: 0,
            maxValue: {maxPrice + 5}
        }},
          colors: {colors},
          focusTarget: 'category' 
        }};

        var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

        chart.draw(data, options);
      }}
    </script>
    """

    cursor.close()
    connection.close()
    return script

def main():
    print(get_price_history(1877))

if __name__ == "__main__":
    main()