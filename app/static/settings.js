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
        let raw = document.getElementById("combinations").value
            .trim()
            .split("\n")
            .map(line => line.trim())
            .filter(line => line !== "");

        let combinations = [];

        for (var i = 0; i < raw.length; i++) {
            let line = raw[i].trim();
            if (line === "") {
                continue;
            }
            let split = line.split(",");
            if (split.length === 3) {
                let pair = [parseInt(split[0].trim()), parseInt(split[1].trim()), parseInt(split[2].trim())];
                combinations.push(pair);
            } else {
                throw new Error("Invalid combination format.");
            }
        }

        return combinations;

    } catch (error) {
        alert("Invalid route settings format. \nCheck for empty lines or ensure each line has three comma-separated values.");
        throw error;
    }
}

function gatherScannerData() {

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
            devices: sget("transit_devices"),
            url: get("transit_url")
        }
    }
    return data;
}

function submitScannerConfig() {
    console.log("submitting data scanner");

    formData = gatherScannerData();

    console.log(formData);
    fetch('/scanner', {
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

function gatherTransitData() {

    function get(name) {
        return document.getElementById(name).value;
    }

    function iget(name) {
        return parseInt(get(name))
    }

    let data = {
        refresh_time: iget("refresh_time"),
        min_transit_time: iget("min_transit_time"),
        max_transit_time: iget("max_transit_time"),
        moving_avg: iget("moving_avg"),
        calculation_mode: iget("calculation_mode"),
        storage_time: iget("storage_time"),
        combinations: getCombinations()
    }
    return data;
}

function submitTransitConfig() {
    console.log("submitting data transit");

    formData = gatherTransitData();

    console.log(formData);
    fetch('/transit', {
        method: 'POST',
        body: JSON.stringify(formData),
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
    .then(async response => {
        const data = await response.json();
        message = data.message || data.error || "No response message";

        if (response.ok) {
            alert("Success: " + message);
            window.location.replace(window.location.pathname);
        } else {
            alert("Error: " + message);
        }
    })
}

function copyUniqueIDs() {
    try {
        const raw = document.getElementById("combinations").value.trim().split("\n");
        const uniqueIDs = new Set();

        raw.forEach(line => {
            const parts = line.trim().split(",");
            if (parts.length >= 2) {
                const id1 = parseInt(parts[0].trim(), 10);
                const id2 = parseInt(parts[1].trim(), 10);
                if (!isNaN(id1)) uniqueIDs.add(id1);
                if (!isNaN(id2)) uniqueIDs.add(id2);
            }
        });

        if (uniqueIDs.size === 0) {
            alert("No valid IDs found.");
            return;
        }

        const sortedList = Array.from(uniqueIDs).sort((a, b) => a - b).join(",");

        // Fallback method using a temporary textarea
        const tempArea = document.createElement("textarea");
        tempArea.value = sortedList;
        document.body.appendChild(tempArea);
        tempArea.select();
        document.execCommand("copy");
        document.body.removeChild(tempArea);

        alert("Copied unique IDs to clipboard:\n" + sortedList);
    } catch (err) {
        console.error("Error in copyUniqueIDsFromPairs:", err);
        alert("An error occurred while copying unique IDs.");
    }
}
