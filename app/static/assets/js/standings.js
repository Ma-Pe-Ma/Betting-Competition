var chartContainer = document.getElementById("chartContainer");
var chart;

function toogleDataSeries(e){
    if (typeof(e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
        e.dataSeries.visible = false;
    } else{
        e.dataSeries.visible = true;
    }
    chart.render();
}

const isDarkMode = () => window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
var theme = localStorage.getItem("theme");
theme = (theme == "dark" || theme == "light") ? `${theme}2` : (isDarkMode() ? "dark2" : "light2");

fetch('/standings.json')
.then(response => response.json())
.then(data => {
    var graphData = []

    for (user of Object.values(data)) {
        var dataPoints = []

        for (day of Object.values(user['days'])) {
            dataPoints.push({
                x: new Date(day['year'], day['month'], day['day']),
                y: day['point']
            });
        }

        graphData.push({
            type : "line",
            axisYType: "secondary",
            name: user['username'],
            showInLegend: true,
            markerSize: 0,
            yValueFormatString: ",###",
            dataPoints: dataPoints
        });
    }

    chart = new CanvasJS.Chart("chartContainer", {
        theme: theme,
        title: {
            text : chartContainer.getAttribute("data-title")
        },
        axisX: {
            valueFormatString: "MMM-DD",
            labelFontSize: 10,
            //tickLength: 1,f
            intervalType: "day",
            interval: 1
        },
        axisY2: {
            title: "",
            //prefix: "$",
            suffix: chartContainer.getAttribute("data-unit")
        },
        toolTip: {
            shared: true
        },
        legend: {
            cursor: "pointer",
            verticalAlign: "top",
            horizontalAlign: "center",
            dockInsidePlotArea: true,
            itemclick: toogleDataSeries
        },

        data : graphData
    });

    chart.render();
})