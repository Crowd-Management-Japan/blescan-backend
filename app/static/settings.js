function splitStringtoArray(inputString) {
    if (inputString == "") {
        return [];
    }
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

function formatFormData(form) {

    let use_internet = form.get("use_internet") == "on"
    let use_zigbee = form.get("use_zigbee") == "on"

    let format = {
        ids: splitStringtoArray(form.get("ids")),
        internet: {
            use_internet: use_internet,
            url: form.get("url"),
            ids: splitStringtoArray(form.get("internet"))
        },
        zigbee: {
            use_zigbee: use_zigbee,
            coordinator: parseInt(form.get("zigbee_coordinator")),
            internet: splitStringtoArray(form.get("zigbee_internet")),
            ids: splitStringtoArray(form.get("zigbee_ids"))
        }
    }


    return format;  // For example, returning true for valid data
}

function submitForm(event) {
    event.preventDefault(); // Prevents the form from submitting in the traditional way

    var formData = new FormData(document.getElementById('settings_form'));

    formData = formatFormData(formData);

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

    /*
    fetch('/setup', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the server
        console.log('Server Response:', data);
    })
    .catch(error => {
        // Handle errors
        console.error('Error:', error);
    });
    */
}

// Attach the submitForm function to the form's submit event
document.getElementById('settings_form').addEventListener('submit', submitForm);