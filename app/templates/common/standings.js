<script>
   window.onload = function () {

    var chart = new CanvasJS.Chart("chartContainer", {
        title: {
            text: "{{graph_title}}"
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
            suffix: " {{bet_unit}}"
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

        data: [
        {% for player in players %}
        {
            type:"line",
            axisYType: "secondary",
            name: "{{player.nick}}",
            showInLegend: true,
            markerSize: 0,
            yValueFormatString: ",###",
            dataPoints: [
                {% for day in player.days %}
                {x: new Date({{day.year}}, {{day.month}}, {{day.day}} ), y:{{day.point}}},
                {% endfor %}
            ]
        },
        {% endfor %}
        ]
    });
    chart.render();

    function toogleDataSeries(e){
        if (typeof(e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
            e.dataSeries.visible = false;
        } else{
            e.dataSeries.visible = true;
        }
        chart.render();
    }

    }
</script>