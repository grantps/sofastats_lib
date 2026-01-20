//Details on ticks etc http://www.ibm.com/developerworks/web/library/wa-moredojocharts/

// BAR ***************************************************************************************
makeBarChart = function(chartname, series, conf){
    nChart = conf["n_records"];
    nChartFontColour = conf["plot_font_color"]
    /*chartwide function setting - have access to val.element (Column), val.index (0), val.run.data (y_vals), shape, x, y, chart, plot, hAxis, eventMask, type, event
    val.run has chart, group, htmlElements, dirty, stroke, fill, plot, data, dyn, name
    val.run = val.run.chart.series[0]
    val.run.chart has margins, stroke, fill, delayInMs, theme, axes, stack, plots, series, runs, dirty,coords,node,surface,dim,offsets,plotArea AND any other variables I put in with the options - the third parameter of addSeries().
    val.run.data has 0,1,2,3,4 etc such that val.run.data[0] is the y-val for the first item  */
    var getTooltip = function(val){
        var tip = val.run.yLbls[val.index];
        return tip;
    };
    var dc = dojox.charting;
    var mychart = new dc.Chart2D(
        chartname,
        {margins:
            {l: conf["left_margin_offset"],
             t: 10,
             r: 10,
             b: 10+conf["axis_label_drop"]},
        yTitleOffset: conf["y_axis_title_offset"]});
    var sofa_theme = new dc.Theme({
        chart:{
	        stroke: null,
        	fill: conf["chart_background_color"],
	        pageStyle: null // suggested page style as an object suitable for dojo.style()
	    },
	    plotarea:{
	        stroke: null,
	        fill: conf["plot_background_color"]
	    },
	    axis:{
	        stroke:	{ // the axis itself
	            color: null,
	            width: null
	        },
            tick: {	// used as a foundation for all ticks
	            color:     conf["axis_font_color"],
	            position:  "center",
	            fontColor: conf["axis_font_color"]
	        },
	        majorTick:	{ // major ticks on axis, and used for major gridlines
	            width:  conf["grid_line_width"],
	            length: 6,
                color: conf["major_grid_line_color"]
	        },
	        minorTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.8,
	            length: 3
	        },
	        microTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.5,
	            length: 1
	        }
	    }
    });
    mychart.setTheme(sofa_theme);
    mychart.addAxis("x",
        {title: conf["x_axis_title"],
         labels: conf["x_axis_numbers_and_labels"],
         minorTicks: conf["has_minor_ticks"],
         font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial",
         rotation: conf["axis_label_rotate"]
    });
    mychart.addAxis("y",
       {title: conf["y_axis_title"],
        vertical: true,
        includeZero: true,
        max: conf["y_axis_max"],
        font: "normal normal normal 10pt Arial",
        fontWeight: 12
    });
    mychart.addPlot("grid",
        {type: "Grid",
         hMajorLines: true,
         hMinorLines: false,
         vMajorLines: false,
         vMinorLines: false }
    );
    mychart.addPlot("default",
        {type: "ClusteredColumns",
         gap: conf["x_gap"],
         shadows: {dx: 12, dy: 12}}
    );
    var i
    for (i in series){
        mychart.addSeries(series[i]["label"], series[i]["vals"], series[i]["options"]);
    }
    var anim_a = new dc.action2d.Highlight(mychart, "default", {
        highlight: conf["highlight"],
        duration: 450,
        easing:   dojo.fx.easing.sineOut
    });
    var anim_b = new dc.action2d.Shake(mychart, "default");
    var anim_c = new dc.action2d.Tooltip(mychart, "default", {text: getTooltip,
        tooltipBorderColour: conf["tool_tip_border_color"],
        connectorStyle: conf["connector_style"]});
    mychart.render();
    var legend = new dojox.charting.widget.Legend({chart: mychart, horizontal: 6}, "legend_for_" + chartname);
}

// PIE ***************************************************************************************
makePieChart = function(chartname, slices, conf){
    nChartFontColour = conf["plot_font_color"]
    nChart = conf["n_records"];
    var pieStroke = "#8b9b98";
    var dc = dojox.charting;
    var mychart = new dc.Chart2D(chartname);
    var sofa_theme = new dc.Theme({
		colors: conf["slice_colors"],
        chart: {
	        stroke: null,
        	fill: null,
	        pageStyle: null // suggested page style as an object suitable for dojo.style()
	    },
		plotarea: {
			fill: conf["plot_background_color"]
		},
	    axis:{
	        stroke:	{ // the axis itself
	            color: null,
	            width: null
	        }
	    }
    });
    mychart.setTheme(sofa_theme);
    mychart.addPlot("default", {
            type: "Pie",
            font: "normal normal " + conf["slice_font_size"] + "px Arial",
            fontColor: conf["plot_font_color"],
            labelOffset: conf['label_offset'],
            radius: conf['radius']
        });

    var pieSeries = Array();
    var i;
    for (i in slices){
        pieSeries[i] =
        {
            y: slices[i]["val"],
            text: slices[i]["label"],
            stroke: pieStroke,
            tooltip: slices[i]["tool_tip"]
        }
    }
    mychart.addSeries("Series A", pieSeries);
    var anim_a = new dc.action2d.MoveSlice(mychart, "default");
    var anim_b = new dc.action2d.Highlight(mychart, "default", {
        highlight: conf["highlight"],
        duration: 450,
        easing:   dojo.fx.easing.sineOut
    });
    var anim_c = new dc.action2d.Tooltip(mychart, "default",
        {tooltipBorderColour: conf['tool_tip_border_color'],
         connectorStyle: conf['connector_style']});
    mychart.render();
}

function zeropad_date(num){
    if (num < 10) {
        return "0" + num
    } else {
        return num
    }
}

// A single parameter function to get labels from epoch milliseconds
function labelfTime(o)
{
   var dt = new Date();
   dt.setTime(o);
   var d = dt.getFullYear() + "-" + zeropad_date(dt.getMonth()+1) + "-" + zeropad_date(dt.getDate());
   //console.log(o+"="+d);
   return d;
}

// LINE ***************************************************************************************
makeLineChart = function(chartname, series, conf){
    nChartFontColour = conf["plot_font_color"]
    nChart = conf["n_records"];
    var getTooltip = function(val){
        var tip = val.run.yLbls[val.index];
        return tip;
    };
    var dc = dojox.charting;
    var mychart = new dc.Chart2D(chartname,
        {margins: {
            l: conf['left_margin_offset'],
            t: 10,
            r: 10,
            b: 10+conf['axis_label_drop']},
            yTitleOffset: conf['y_axis_title_offset']});
    var sofa_theme = new dc.Theme({
        chart:{
	        stroke: null,
        	fill: conf["chart_background_color"],
	        pageStyle: null // suggested page style as an object suitable for dojo.style()
	    },
	    plotarea:{
	        stroke: null,
	        fill: conf["plot_background_color"]
	    },
	    axis:{
	        stroke:	{ // the axis itself
	            color: null,
	            width: null
	        },
            tick: {	// used as a foundation for all ticks
	            color:     conf["axis_font_color"],
	            position:  "center",
	            fontColor: conf["axis_font_color"]
	        },
	        majorTick:	{ // major ticks on axis, and used for major gridlines
	            width:  conf['grid_line_width'],
	            length: 6,
                color: conf["major_grid_line_color"]
	        },
	        minorTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  2,
	            length: 4,
                color: conf["major_grid_line_color"]
	        },
	        microTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  1.7,
	            length: 3,
                color: null
	        }
	    }
    });
    mychart.setTheme(sofa_theme);
    // x-axis
    var xaxis_conf = {
        title: conf['x_axis_title'],
        font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial",
        rotation: conf['axis_label_rotate'],
        minorTicks: conf['has_minor_ticks'],
        microTicks: conf['has_micro_ticks'],
        minorLabels: conf['has_minor_ticks']
    };
    if (conf['is_time_series']) {
        xaxis_conf.labelFunc = labelfTime;
    } else {
        xaxis_conf.labels = conf["x_axis_numbers_and_labels"];
    };
    mychart.addAxis("x", xaxis_conf);
    // y-axis
    mychart.addAxis("y", {title: conf['y_axis_title'],
                    vertical: true, includeZero: true,
                    max: conf["y_axis_max"],
                    font: "normal normal normal 10pt Arial", fontWeight: 12
    });
    mychart.addPlot("default", {type: "Lines", markers: true, shadows: {dx: 2, dy: 2, dw: 2}});
    mychart.addPlot("unmarked", {type: "Lines", markers: false});
    mychart.addPlot("curved", {type: "Lines", markers: false, tension: "S"});
    mychart.addPlot("grid", {type: "Grid", vMajorLines: false});
    var i
    for (i in series){
        mychart.addSeries(series[i]["label"], series[i]["vals"], series[i]["options"]);
    }
    var anim_a = new dc.action2d.Magnify(mychart, "default");
    var anim_b = new dc.action2d.Tooltip(mychart, "default", {text: getTooltip,
        tooltipBorderColour: conf['tool_tip_border_color'], connectorStyle: conf['connector_style']});
    mychart.render();
    var legend = new dojox.charting.widget.Legend({chart: mychart}, "legend_for_" + chartname);
}

// AREA ***************************************************************************************
makeAreaChart = function(chartname, series, conf){
    nChartFontColour = conf["plot_font_color"]
    nChart = conf["n_records"];
    var getTooltip = function(val){
        var tip = val.run.yLbls[val.index];
        return tip;
    };
    var dc = dojox.charting;
    var mychart = new dc.Chart2D(chartname,
        {margins: {
            l: conf['left_margin_offset'],
            t: 10,
            r: 10,
            b: 10+conf['axis_label_drop']},
        yTitleOffset: conf['y_axis_title_offset']});
    var sofa_theme = new dc.Theme({
        chart:{
	        stroke: null,
        	fill: null,
	        pageStyle: null // suggested page style as an object suitable for dojo.style()
	    },
	    plotarea:{
	        stroke: null,
	        fill: conf["plot_background_color"]
	    },
	    axis:{
	        stroke:	{ // the axis itself
	            color: null,
	            width: null
	        },
            tick: {	// used as a foundation for all ticks
	            color:     conf["axis_font_color"],
	            position:  "center",
	            fontColor: conf["axis_font_color"]
	        },
	        majorTick:	{ // major ticks on axis, and used for major gridlines
	            width:  conf['gridline_width'],
	            length: 6,
                color: conf["major_grid_line_color"]
	        },
	        minorTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  2,
	            length: 4,
                color: conf["major_grid_line_color"]
	        },
	        microTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  1.7,
	            length: 3,
                color: "black"
	        }
	    }
    });
    mychart.setTheme(sofa_theme);
    // x-axis
    var xaxis_conf = {
        title: conf['x_axis_title'],
        font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial",
        rotation: conf['axis_label_rotate'],
        minorTicks: conf['has_minor_ticks'],
        microTicks: conf['has_micro_ticks'],
        minorLabels: conf['has_minor_ticks']
    };
    if (conf['time_series']) {
        xaxis_conf.labelFunc = labelfTime;
    } else {
        xaxis_conf.labels = conf["x_axis_numbers_and_labels"];
    };
    mychart.addAxis("x", xaxis_conf);
    // y-axis
    mychart.addAxis("y", {title: conf['y_axis_title'],  // normal normal bold
                    vertical: true, includeZero: true,
                    max: conf["y_axis_max"],
                    font: "normal normal normal 10pt Arial", fontWeight: 12
    });
    mychart.addPlot("default", {type: "Areas", lines: true, areas: true, markers: true});
    mychart.addPlot("unmarked", {type: "Areas", lines: true, areas: true, markers: false});
    mychart.addPlot("grid", {type: "Grid", vMajorLines: false});
    var i
    for (i in series){
        mychart.addSeries(series[i]["label"], series[i]["vals"], series[i]["options"]);
    }
    var anim_a = new dc.action2d.Magnify(mychart, "default");
    var anim_b = new dc.action2d.Tooltip(mychart, "default",
        {text: getTooltip,
         tooltipBorderColour: conf['tool_tip_border_color'],
         connectorStyle: conf['connector_style']});
    mychart.render();
}

// HISTOGRAM ***************************************************************************************
makeHistogram = function(chartname, data_spec, conf){
    nChartFontColour = conf["plot_font_color"]
    nChart = conf["n_records"];
    // chartwide function setting - have access to val.element (Column), val.index (0), val.run.data (y_vals)
    var getTooltip = function(val){
        return "Values: " + data_spec["bin_labels"][val.index] + "<br>" + conf['y_axis_title'] + ": " + val.y;
    };
    var dc = dojox.charting;
    var mychart = new dc.Chart2D(chartname,
       {margins: {
            l: conf['left_margin_offset'],
            t: 10,
            r: 10,
            b: 10},
        yTitleOffset: conf['y_axis_title_offset']});

    var sofa_theme = new dc.Theme({
        chart:{
	        stroke: null,
            fill: null,  //conf["chart_bg"],
	        pageStyle: null // suggested page style as an object suitable for dojo.style()
	    },
	    plotarea:{
	        stroke: null,
	        fill: conf["plot_background_color"]
	    },
	    axis:{
	        stroke:	{ // the axis itself
	            color: null,
	            width: null
	        },
            tick: {	// used as a foundation for all ticks
	            color:     conf["axis_font_color"],
	            position:  "center",
	            fontColor: conf["axis_font_color"]
	        },
	        majorTick:	{ // major ticks on axis, and used for major gridlines
	            width:  conf['grid_line_width'],
	            length: 6,
                color: conf["major_grid_line_color"]
	        },
	        minorTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.8,
	            length: 3
	        },
	        microTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.5,
	            length: 1
	        }
	    }
    });
    mychart.setTheme(sofa_theme);
    mychart.addAxis("x", {title: data_spec["series_label"],
        labels: conf["blank_x_axis_numbers_and_labels"], minorTicks: false, microTicks: false,
        font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial"
    });
    mychart.addAxis("x2", {
        min: conf["x_axis_min_val"],
        max: conf["x_axis_max_val"],
        minorTicks: conf['has_minor_ticks'],
        font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial"
    });
    mychart.addAxis("y", {
        title: conf['y_axis_title'],  // normal normal bold
        max: conf["y_axis_max_val"],
        vertical: true, includeZero: true, font: "normal normal normal 10pt Arial", fontWeight: 12
    });
    mychart.addPlot("normal", {type: "Lines", markers: true, shadows: {dx: 2, dy: 2, dw: 2}}); // must come first to be seen!
    mychart.addPlot("default", {type: "Columns", gap: 0, shadows: {dx: 12, dy: 12}});
    mychart.addPlot("grid", {type: "Grid", vMajorLines: false});
    mychart.addPlot("othergrid", {type: "Areas", hAxis: "x2", vAxis: "y"});
    mychart.addSeries(data_spec["series_label"], data_spec["y_vals"], data_spec["style"]);
    if(conf['show_normal_curve'] == true){
        mychart.addPlot("normal", {type: "Lines", markers: false, shadows: {dx: 2, dy: 2, dw: 2}});
        mychart.addSeries("Normal Dist Curve", data_spec["norm_y_vals"], data_spec["norm_style"]);
    }
    var anim_a = new dc.action2d.Highlight(mychart, "default", {
        highlight: conf["highlight"],
        duration: 450,
        easing:   dojo.fx.easing.sineOut
    });
    var anim_b = new dc.action2d.Shake(mychart, "default");
    var anim_c = new dc.action2d.Tooltip(
        mychart,
        "default",
        {text: getTooltip,
         tooltipBorderColour: conf['tool_tip_border_color'],
         connectorStyle: conf['connector_style']});
    mychart.render();
}

// SCATTERPLOT ***************************************************************************************
makeScatterplot = function(chartname, series, conf){
    nChartFontColour = conf["plot_font_color"]
    nChart = conf["n_records"];
    // chartwide function setting - have access to val.element (Column), val.index (0), val.run.data (y_vals)
    var getTooltip = function(val){
        return "(" + conf['x_axis_title'] + ": " + val.x + ", " + conf['y_axis_title'] + ": " + val.y + ")";
    };
    var dc = dojox.charting;
    var mychart = new dc.Chart2D(
        chartname,
        {margins:
            {l: conf['left_margin_offset'],
             t: 10,
             r: 10,
             b: 10+conf['axis_label_drop']},
         yTitleOffset: conf['y_axis_title_offset']});
    var sofa_theme = new dc.Theme({
        chart:{
	        stroke: null,
        	fill: conf['chart_background_color'],
	        pageStyle: null // suggested page style as an object suitable for dojo.style()
	    },
	    plotarea:{
	        stroke: null,
	        fill: conf["plot_background_color"]
	    },
	    axis:{
	        stroke:	{ // the axis itself
	            color: null,
	            width: null
	        },
            tick: {	// used as a foundation for all ticks
	            color:     conf["axis_font_color"],
	            position:  "center",
	            fontColor: conf["axis_font_color"]
	        },
	        majorTick:	{ // major ticks on axis, and used for major gridlines
	            width:  conf["grid_line_width"],
	            length: 6,
                color: conf["major_grid_line_color"]
	        },
	        minorTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.8,
	            length: 3
	        },
	        microTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.5,
	            length: 1
	        }
	    }
    });
    mychart.setTheme(sofa_theme);
    mychart.addAxis("x", {title: conf['x_axis_title'],
        min: conf["x_axis_min_val"], max: conf["x_axis_max_val"],
        minorTicks: conf['has_minor_ticks'], microTicks: false,
        font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial"
    });
    mychart.addAxis("y", {title: conf['y_axis_title'],
        min: conf["y_axis_min_val"], max: conf["y_axis_max_val"],
        vertical: true, font: "normal normal normal 10pt Arial", fontWeight: 12
    });
    // plot line first so on top
    if(conf['show_regression_line'] == true){
        mychart.addPlot("regression", {type: "Lines", markers: false, shadows: {dx: 2, dy: 2, dw: 2}});
        for (i in series){
            try {
                mychart.addSeries(series[i]["label"], series[i]["xy_pairs"], series[i]["options"]);
            } catch(err) {
                /*do nothing*/
            }
        }
    }
    mychart.addPlot("default", {type: "Scatter"});
    mychart.addPlot("grid", {type: "Grid", vMajorLines: true});
    var i
    for (i in series){
        mychart.addSeries(series[i]["label"], series[i]["xy_pairs"], series[i]["options"]);
    }
    var anim_a = new dc.action2d.Magnify(mychart, "default");
    var anim_b = new dc.action2d.Tooltip(mychart, "default",
       {text: getTooltip,
        tooltipBorderColour: conf['tool_tip_border_color'],
        connectorStyle: conf['connector_style']});
    mychart.render();
    var legend = new dojox.charting.widget.Legend({chart: mychart}, "legend_for_" + chartname);
    var anim_a = new dc.action2d.Highlight(mychart, "default", {
        highlight: conf["highlight"],
        duration: 450,
        easing:   dojo.fx.easing.sineOut
    });
    var anim_b = new dc.action2d.Shake(mychart, "default");
    var anim_c = new dc.action2d.Tooltip(mychart, "default", {text: getTooltip,
        tooltipBorderColour: conf['tool_tip_border_color'],
        connectorStyle: conf['connector_style']});
    mychart.render();
}

// BOX ***************************************************************************************
makeBoxAndWhisker = function(chartname, series, series_conf, conf){
    nChartFontColour = conf["plot_font_color"]
    nChart = conf["n_records"];
    borderWidth = conf["border_width"]  // borderWidth is now available as such inside sofastats_dojo(_minified).js
    // chart-wide function setting - have access to val.element (Column), val.index (0), val.run.data (y_vals)
    var getTooltip = function(val){
        return val.y;
    };
    var dc = dojox.charting;
    var mychart = new dc.Chart2D(
        chartname,
        {margins:
            {l: conf['left_margin_offset'],
             t: 10,
             r: 10,
             b: 10+conf['axis_label_drop']},
         yTitleOffset: conf['y_axis_title_offset']});
    var sofa_theme = new dc.Theme({
        chart:{
	        stroke:    null,
        	fill:      conf['chart_background_color'],
	        pageStyle: null // suggested page style as an object suitable for dojo.style()
	    },
	    plotarea:{
	        stroke: null,
	        fill:   conf["plot_background_color"]
	    },
	    axis:{
	        stroke:	{ // the axis itself
	            color: conf['plot_font_color'],
	            width: null
	        },
            tick: {	// used as a foundation for all ticks
	            color:     conf["axis_font_color"],
	            position:  "center",
	            fontColor: conf['axis_font_color']
	        },
	        majorTick:	{ // major ticks on axis, and used for major gridlines
	            width:  conf['grid_line_width'],
	            length: 6,
                color:  conf['axis_font_color'] // we have vMajorLines off so we don't need to match grid color e.g. null
	        },
	        minorTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.8,
	            length: 3
	        },
	        microTick:	{ // minor ticks on axis, and used for minor gridlines
	            width:  0.5,
	            length: 1
	        }
	    }
    });
    mychart.setTheme(sofa_theme);
    mychart.addPlot("default", {type: "Boxplot", markers: true});  // the link to the sofastats_dojo(_minified).js boxplot definition as exposed by dojo.provide("dojox.charting.plot2d.Boxplot");
    mychart.addPlot("grid", {type: "Grid", vMajorLines: false});
    mychart.addAxis(
        "x",
        {title: conf['x_axis_title'],
         min: 0.5,
         max: conf["x_axis_max_val"],
         majorTicks: true,
         minorTicks: conf['has_minor_ticks'],
         labels: conf["x_axis_numbers_and_labels"],
         font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial",
         rotation: conf['axis_label_rotate']});
    mychart.addAxis(
        "y",
        {title: conf['y_axis_title'],
         vertical: true,
         min: conf["y_axis_min_val"],
         max: conf["y_axis_max_val"],
         majorTicks: true,
         minorTicks: true,
         font: "normal normal normal " + conf["x_axis_font_size"] + "pt Arial"
         });
    var i
    for (i in series){  // each item in series is a box (one per x value per data series)
        mychart.addSeries('dummy_label_' + i, [], series[i]);  // Dojo expects a label and data but we won't use them in boxplot so dummy vals used
    }
    var anim_a = new dc.action2d.Highlight(mychart, "default", {
        highlight: conf["highlight"],
        duration: 450,
        easing:   dojo.fx.easing.sineOut
    });
    var anim_b = new dc.action2d.Tooltip(
        mychart,
        "default",
        {text: getTooltip,
         tooltipBorderColour: conf['tool_tip_border_color'],
         connectorStyle: conf['connector_style']});
    mychart.render();
    if (series_conf.length > 1) {
        // dummy chart needed for automatic legend creation to work from - will be invisible
        // Needs stroke (text), label (to display), and fill (colour of boxplot)
        console.log(chartname)
        var dummychart = new dc.Chart2D("dummy_" + chartname);  // must use _this_ exact name as div id so legend can be put there
        dummychart.addPlot("default", {type: "ClusteredColumns"});
        for (i in series_conf){  // Dojo expects data so we supply dummy data [1,2] - the only things we supply are what is required to build legend
            dummychart.addSeries(series_conf[i]["seriesLabel"], [1,2], series_conf[i]["seriesStyle"]);
        }
        dummychart.render();
        var legend = new dojox.charting.widget.Legend({chart: dummychart}, "legend_for_" + chartname);
    }
}
