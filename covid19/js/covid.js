function createStateCharts(state, stateAbbreviation) {
    createStateChart(state, stateAbbreviation, 'deathIncrease', 'New deaths', 'state-deaths');
    createStateChart(state, stateAbbreviation, 'positiveIncrease', 'New cases', 'state-positives');
    createStateChart(state, stateAbbreviation, 'hospitalizedIncrease', 'New hospitalizations', 'state-hospitalized');
}

function createStateChart(state, stateAbbreviation, apiField, heading, chartID) {
    var url = 'https://api.covidtracking.com/v1/states/' + stateAbbreviation.toLowerCase() + '/daily.json';
    if (stateAbbreviation.toLowerCase() == 'us') {
        url = 'https://api.covidtracking.com/v1/us/daily.json';
    }


    fetch(url, {method: 'get'})
    .then((response) => response.json())
    .then(function(days) {
        // Assumes results are sorted in descending order by date.
        var labels = [];
        var deathData = [];
        for (var k = 0; k < days.length; k++) {
            // Assumes YYYYMMDD int
            var date = '' + days[days.length - k -1]['date'];
            date = date.slice(0, 4) + '-' + date.slice(4, 6) + '-' + date.slice(-2);
            labels.push(date);
            deathData.push({meta: date, value: days[days.length - k - 1][apiField]});
        }
        var data = { labels: labels, series: [deathData] };
        var options = { seriesBarDistance: 25,
                        axisX: { labelInterpolationFnc: function(value, index) {
                                    return index % 5 === 0 ? value : null;
                                }
                        },
                      };

        var chart = new Chartist.Bar(`#${chartID}`, data, options);

        // Tooltips setup
        // https://stackoverflow.com/questions/34562140/how-to-show-label-when-mouse-over-bar
        chart.on('created', function(bar) {
            var toolTipSelector = `#${chartID}-tooltip`;
            $(`.${chartID} .ct-bar`).on('mouseenter', function(e) {
                var value = $(this).attr('ct:value');
                var label = $(this).attr('ct:meta');
                var caption = `<b>Date:</b> ${label}<br><b>${heading} (${state})</b> ${value}`;
                $(toolTipSelector).html(caption);
                $(toolTipSelector).parent().css({position: 'relative'});
                // bring to front, https://stackoverflow.com/questions/3233219/is-there-a-way-in-jquery-to-bring-a-div-to-front
                $(toolTipSelector).parent().append($(toolTipSelector));

                var x = e.clientX;
                var y = e.clientY;
                $(toolTipSelector).css({top: y, left: x, position:'fixed', display: 'block'});
            });

            $(`.${chartID} .ct-bar`).on('mouseout', function() {
                $(toolTipSelector).css({display: 'none'});
            });
        });

        $(`#${chartID}-title`).html(`${heading}`);
    })

    // Log the error if anything went wrong during the fetch.
    .catch(function(error) {
        console.log(error);
    });
}

function init() {
    var url = 'https://api.covidtracking.com/v1/states/info.json';
    fetch(url, {method: 'get'})
    .then((response) => response.json())
    .then(function(states) {
        $('#state-select').append($('<option>', { value: 'US', text: 'United States' }));
        $.each(states, function (i, state) {
            $('#state-select').append($('<option>', { 
                value: state['state'], // dumb API field naming; should be 'abbreviation'
                text : state['name']
            }));
        });

        $('#state-select').change(function() {
            createStateCharts($('#state-select option:selected').text(), $('#state-select').val());
        });

        $('#state-select').val('MN');
        createStateCharts('Minnesota', 'MN');
    })
    .catch(function(error) {
        console.log(error);
    });
}

init();

/*
{
    "date":20200607,
    "state":"MN",
    "positive":27886,
    "negative":316317,
    "pending":null,
    "hospitalizedCurrently":450,
    "hospitalizedCumulative":3367,
    "inIcuCurrently":199,
    "inIcuCumulative":1044,
    "onVentilatorCurrently":null,
    "onVentilatorCumulative":null,
    "recovered":22992,
    "dataQualityGrade":"A",
    "lastUpdateEt":"6/6/2020 17:00",
    "dateModified":"2020-06-06T17:00:00Z",
    "checkTimeEt":"06/06 13:00",
    "death":1197,
    "hospitalized":3367,
    "dateChecked":"2020-06-06T17:00:00Z",
    "fips":"27",
    "positiveIncrease":385,
    "negativeIncrease":10334,
    "total":344203,
    "totalTestResults":344203,
    "totalTestResultsIncrease":10719,
    "posNeg":344203,
    "deathIncrease":16,
    "hospitalizedIncrease":31,
    "hash":"5f4eb67ca77d3ebc7d7b111b20fbd5476b182a45",
    "commercialScore":0,
    "negativeRegularScore":0,
    "negativeScore":0,
    "positiveScore":0,
    "score":0,
    "grade":""
}
*/

