function drawPlot(data) {
    let svg = d3.select('svg'),
        g = svg.select('g'),
        width = parseFloat(svg.style('width')) -
            (parseFloat(svg.style('padding-left')) + parseFloat(svg.style('padding')) + parseFloat(svg.style('margin'))*2),
        height = parseFloat(svg.style('height')) -
            (parseFloat(svg.style('padding')) + parseFloat(svg.style('margin'))) * 2,
        x = d3.scaleLinear()
            .domain([0, data.lfp.length/1000])
            .range([0,  width]);

    function spikeTrain(spikes) {
        let y = d3.scaleLinear()
            .domain([0, spikes.length])
            .rangeRound([height*0.48, 0]);
        let spikeTrainSelection = d3.select('#spike-train')
            .selectAll('g').data(spikes);
        spikeTrainSelection.exit().remove();
        let units = spikeTrainSelection.enter().append('g').merge(spikeTrainSelection)
            .selectAll('line')
            .data((d,i) => d.map(e => [e,i]))
        units.enter().append('line').merge(units)
            .attr('class', 'spike')
            .attr('x1', d => x(d[0]))
            .attr('x2', d => x(d[0]))
            .attr('y1', d => y(d[1]+0.05))
            .attr('y2', d => y(d[1]+0.95));
        units.exit().remove();
        g.select('#axis-spike')
            .attr('class', 'axis')
            .call(d3.axisLeft(y));
    }

    function lfpTrace(lfp) {
        let y = d3.scaleLinear()
            .domain(d3.extent(lfp))
            .rangeRound([height*0.98, height*0.52]);
        let lineFunc = d3.line()
            .x((d, i) => x(i/1000))
            .y(d => y(d));
        let lfpSelection = d3.select('#lfp-trace')
            .selectAll('path').data([lfp]);
        lfpSelection.enter().append('path').merge(lfpSelection)
            .attr('class', 'lfp')
            .attr('d', lineFunc);
        lfpSelection.exit().remove();
        g.select('#axis-lfp')
            .attr('class', 'axis')
            .call(d3.axisLeft(y));
    }

    function trialEvents(events) {
        let colorMap = {
            'fixate': 'red',
            'noise': 'green',
            'shape': 'blue',
            'saccade': 'purple'
        };
        let root = d3.select('#events');
        let eventLines = root.selectAll('line').data(Object.entries(events));
        eventLines.enter().append('line').merge(eventLines)
            .attr('class', 'event')
            .attr('stroke', d => colorMap[d[0]])
            .attr('x1', d => x(d[1]))
            .attr('x2', d => x(d[1]))
            .attr('y1', _ => 0)
            .attr('y2', _ => height);
        eventLines.exit().remove();

        let annoMap = {
            'fixate': 'F',
            'noise': 'N',
            'shape': 'H',
            'saccade': 'S'
        };
        let eventAnnotations = root.selectAll('text').data(Object.entries(events));
        eventAnnotations.enter().append('text').merge(eventAnnotations)
            .attr('class', 'event-annotation')
            .text(d => annoMap[d[0]])
            .attr('x', d => x(d[1]))
            .attr('y', 0)
            .attr('fill', d => colorMap[d[0]])
        eventAnnotations.exit().remove();
    }

    spikeTrain(data.spikes);
    lfpTrace(data.lfp.map(parseFloat));
    trialEvents(data.events);
    g.select('#axis-bottom')
        .attr('class', 'axis')
        .attr("transform", `translate(0, ${height})`)
        .call(d3.axisBottom(x));
}

function buildQuery(name, params) {
    return encodeURI(name) +
        (params ?
            '?' + Object.keys(params)
                    .map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k])).join('&') :
            '')
}

function formatDate(date) {
    date = new Date(date);
    return new Date(date.getTime() + date.getTimezoneOffset()*60000)
                .toLocaleDateString('en-US',
                                    {weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'});
}

function getPlotData(monkeyName, date, idx, callback) {
    fetch(buildQuery('/trial', {name: monkeyName, date: date, idx: idx}))
        .then(resp => resp.json())
        .then(callback);
}

let controls = new Vue({
    el: '#controls',
    data: {
        monkeyNames: [],
        monkeyName: '',
        dates: [],
        date: '',
        idxs: [],
        idx: {
            idx: '' // HACK: get Vue to recognize 0 -> 0 updates as changes
        }
    },
    methods: {
        onPrev: function() {
            let idxOfIdx = this.idxs.indexOf(this.idx.idx);
            this.idx.idx = this.idxs[Math.max(0, idxOfIdx-1)];
        },
        onNext: function() {
            let idxOfIdx = this.idxs.indexOf(this.idx.idx);
            this.idx.idx = this.idxs[Math.min(this.idxs.length-1, idxOfIdx+1)];
        }
    },
    watch: {
        monkeyName: function(newMonkeyName) {
            fetch(buildQuery('/dates', {name: this.monkeyName}))
                .then(resp => resp.json())
                .then((function(data) {
                    this.dates = data;
                    this.date = data[0];
                }).bind(this));
        },
        date: function(newDate) {
            fetch(buildQuery('/idxs', {name: this.monkeyName, date: this.date}))
                .then(resp => resp.json())
                .then((function(data) {
                    this.idxs = data;
                    this.idx = {idx: data[0]};
                }).bind(this));
        },
        idx: {
            handler: function(newIdx) {
                getPlotData(this.monkeyName, this.date, this.idx.idx, drawPlot);
            },
            deep: true
        }
    }
});

fetch('/names').then(resp => resp.json())
    .then(function(data) {
        controls.monkeyNames = data;
        controls.monkeyName = controls.monkeyNames[0];
    }
);
