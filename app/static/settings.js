function splitStringtoArray(inputString) {
    if (inputString == "" || inputString == null) {
        return [];
    }
    console.log("Splitting string: " + inputString);
    let result = [];
    // remove all spaces first
    inputString.replace(' ', '');
    let groups = inputString.split(',');

    groups.forEach(group => {
        if (group.includes('-')) {
            // If the group contains a range (e.g., "2-4")
            let range = group.split('-');
            let start = parseInt(range[0], 10);
            let end = parseInt(range[1], 10);
            for (let i = start; i <= end; i++) {
                result.push(i);
            }
        } else {
            // If the group is a single number (e.g., "1")
            result.push(parseInt(group, 10));
        }
    });

    return result;
}

function getLocations() {
    try {
        let raw = document.getElementById("textarea_loc").value.split("\n");
        let locations = {};

        for (var i = 0; i < raw.length; i++) {
            let line = raw[i];
            if (line == "") {
                continue;
            }
            let split = line.split(":");
            locations[split[0].trim()] = split[1].trim();
        }

        return locations;
    } catch {
        alert("Invalid location format. Ignoring. \n (Check for empty lines)");
        return {};
    }
}

function getCombinations() {
    try {
        let raw = document.getElementById("textarea_combinations").value.trim().split("\n");
        let combinations = [];

        for (var i = 0; i < raw.length; i++) {
            let line = raw[i].trim();
            if (line === "") {
                continue;
            }
            let split = line.split(",");
            if (split.length === 2) {
                let pair = [parseInt(split[0].trim()), parseInt(split[1].trim())];
                combinations.push(pair);
            } else {
                throw new Error("Invalid combination format.");
            }
        }

        return combinations;
    } catch (error) {
        alert("Invalid combination format. Ignoring.\nCheck for empty lines or ensure each line has two comma-separated values.");
        return [];
    }
}

function gatherData() {

    function get(name) {
        return document.getElementById(name).value;
    }

    function sget(name) {
        return splitStringtoArray(get(name));
    }

    function iget(name) {
        return parseInt(get(name))
    }

    let data = {
        ids: sget("ids"),
        led: document.getElementById("use_led").checked,
        scantime: iget("scantime"),
        locations: getLocations(),
        zigbee: {
            enable: document.getElementById("use_zigbee").checked,
            coordinator: iget("zigbee_coordinator"),
            internet: sget("zigbee_internet"),
            pan: iget("zigbee_pan")
        },
        counting: {
            rssi_threshold: iget("counting_rssi"),
            rssi_close_threshold: iget("counting_close"),
            delta: iget("counting_delta"),
            static_ratio: parseFloat(get("static_ratio")),
            url: get("counting_url")
        },
        beacon: {
            target_id: get("beacon_target_id"),
            scans: iget("beacon_scans"),
            threshold: iget("beacon_threshold"),
            shutdown_id: get("beacon_shutdown")
        },
        transit: {
            delta: iget("transit_delta"),
            combinations: getCombinations(),
            url: get("transit_url")
        }
    }
    return data;
}

function submitForm() {
    console.log("submitting data");

    formData = gatherData();

    console.log(formData);
    fetch('/setup', {
        method: 'POST',
        body: JSON.stringify(formData),
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        redirect: 'follow'
    })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        }).catch(error => {
            console.error('Error:', error);
        })
}
