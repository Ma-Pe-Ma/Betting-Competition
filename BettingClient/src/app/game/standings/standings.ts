import { Component, ViewChild, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, tap, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { CanvasJSAngularChartsModule, CanvasJSChart } from '@canvasjs/angular-charts';

interface DayPoint {
  date: string,
  point: number,
  position_diff: number
}

interface UserStanding {
  username: string,
  imagePath: string,
  days: DayPoint[]
}

@Component({
  selector: 'app-standings',
  imports: [CanvasJSAngularChartsModule],
  templateUrl: './standings.html'
})
export class Standings {
  @ViewChild(CanvasJSChart) chart: CanvasJSChart | undefined;
  chartInstance: any;

  chartOptions = {
      theme: "dark2",
      title: {
          text : 'History of standings'
      },
      axisX: {
          valueFormatString: "MMM-DD",
          labelFontSize: 10,
          intervalType: "day",
          interval: 1
      },
      axisY2: {
          title: "",
          suffix: 'Credit'
      },
      toolTip: {
          shared: true
      },
      legend: {
          cursor: "pointer",
          verticalAlign: "top",
          horizontalAlign: "center",
          dockInsidePlotArea: true,
          itemclick: (e: any) => this.toggleDataSeries(e)
      },

      data: [] as any[]
  }

  standings: any[] = []

  toggleDataSeries(e: any) {
    if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
      e.dataSeries.visible = false;
    } else {
      e.dataSeries.visible = true;
    }
    this.chartInstance.render();
  }

  constructor(private http: HttpClient, private ngZone: NgZone) { 

    let standingsPath = environment.serverAddress + environment.locations.standings;

    this.http.get<UserStanding[]>(standingsPath).pipe(
      map(data => {
        return data.map(standing => {
            let result = {
              type : "line",
              axisYType: "secondary",
              name: standing.username,
              image: standing.imagePath,
              showInLegend: true,
              markerSize: 0,
              yValueFormatString: ",###",
              dataPoints: standing.days.map(day => {
                return { x: new Date(day.date), y: day.point}
              })
            }

            return result;
        });
      }),
      tap(data => {
        this.ngZone.runOutsideAngular(() => {
          this.chartOptions.data = data;
          this.chartInstance.render();
        });

        for (let user of data) {
            let lastDay = user.dataPoints[user.dataPoints.length - 1];
            let penultimateDay = user.dataPoints[user.dataPoints.length - 2];
            this.standings.push({username: user.name, image: user.image, point: lastDay.y, penultimatePoint: penultimateDay.y});
          }

          this.standings
            .sort((a, b) => b.penultimatePoint - a.penultimatePoint)
            .forEach((pos, index) => {
               pos.penultimatePosition = index;
             })

          this.standings.sort((a, b) => b.point - a.point);
        
      }),
      catchError(err => {
        console.error('Error fetching standings: ', err);
        return [];
      })
    ).subscribe();
  }
}
