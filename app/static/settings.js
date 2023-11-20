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
        internet: {
            url: get("url")
        },
        zigbee: {
            enable: get("use_zigbee") == "on",
            coordinator: parseInt(get("zigbee_coordinator")),
            internet: sget("zigbee_internet"),
            pan: parseInt(get("zigbee_pan"))
        },
        counting: {
            rssi_threshold:iget("counting_rssi"),
            rssi_close_threshold: iget("counting_close"),
            delta: iget("counting_delta")
        },
        beacon: {
            target_id: get("beacon_target_id"),
            scans: iget("beacon_scans"),
            threshold: iget("beacon_threshold")
        }
    }
    return data
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