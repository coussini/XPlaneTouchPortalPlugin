const oneId = 'XPlaneTouchPortalPlugin.';
let datarefs = [];
let groups = [];

/* function on load */
/* validate form when the user press "add dataref to result" button */
/* when everything validated, save that to result box */
(function () {
    'use strict';
    window.addEventListener('load', function () {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        let formsThatNeedsValidation = document.getElementsByClassName('needs-validation');
        // Loop over them and prevent submission
        let validation = Array.prototype.filter.call(formsThatNeedsValidation, function (form) {
            form.addEventListener('submit', function (event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
                // If this form is valid, treat a dataref
                if (form.checkValidity() === true) {
                    event.preventDefault();
                    let dataref = document.getElementById('dataref').value;
                    let the_index = document.getElementById('index').value;
                    let group = document.getElementById('group').value;
                    // If there's index entered, append it to the dataref name withing braket
                    if (document.getElementById('index').value.length != 0) {
                        dataref = dataref.concat("[", the_index, "]");
                    }
                    let objet_dataref =
                    {
                        id: oneId.concat(document.getElementById('desc').value.replaceAll(' ', '')),
                        desc: document.getElementById('desc').value,
                        group: document.getElementById('group').value,
                        type: document.getElementById('type').value,
                        value: document.getElementById('value').value,
                        dataref: dataref,
                        comment: document.getElementById('comment').value
                    };
                    console.log(objet_dataref)
                    // save the objet_dataref
                    datarefs.push(objet_dataref);
                    // keep unic group name only
                    let elementExists = groups.includes(group);
                    if (!elementExists) {
                        groups.push(group);
                    }
                    // result list: for displaying datarefs and editing purposes
                    let resultList = document.querySelector('#result-list');
                    resultList.textContent = '\n' + JSON.stringify(datarefs, '\t', 2);
                    // group list: for displaying only
                    let groupList = document.querySelector('#group-list');
                    groupList.textContent = groups;
                    // enable check box button and result box
                    document.getElementById("result-list").disabled = false;
                    document.getElementById("checkme").disabled = false;
                    //reseting the form
                    form.reset();
                    //reseting the form validation
                    form.classList.remove("was-validated");
                }
            }, false);
        });
    }, false);
})();

function evaluate_checkbox() 
{
    if (document.getElementById('checkme').checked) 
    {
        document.querySelector('#save').innerHTML = 'saving to dataref.json';
        document.getElementById('save').disabled = false;
    }
    else 
    {
        document.querySelector('#save').innerHTML = 'check me before saving';
        document.getElementById('save').disabled = true;
    }
}

function invalid_json(message) 
{
    document.getElementById("alert-message").innerHTML = message;
    const alert = document.getElementById("danger-alert");
    alert.style.display = "block";
}

function close_alert_box() 
{
    document.getElementById("alert-message").innerHTML = "";
    const alert = document.getElementById("danger-alert");
    alert.style.display = "none";
}

function download_file()
{
    console.log("downloading process");
    let link = document.createElement("a");
    let begin = '{\n"datarefs": '
    let middle = document.getElementById('result-list').value;
    let [valid, error_message] = isJSON(middle);
    if (valid)
    {
        console.log("JSON is valid");
        /* verify if the dataref patern is ok */
        let object_json = JSON.parse(middle);
        let dataref = object_json[0].dataref;
        let result = dataref.match(/(^([a-zA-Z0-9 _\/]+)\[[0-9]+]$)|(^([a-zA-Z0-9 _\/]+)$)/);
        /* does not match with the pattern */
        if (result == null)
        {
            console.log("bad dataref");
            valid = false;
            error_message = "bad dataref value: "+dataref;         
            console.log(error_message);
            invalid_json(error_message);
        }
    }
    if (valid)
    {
        let end = '\n}';
        let content = begin.concat(middle).concat(end);
        let file = new Blob([content], { type: 'text/plain' });
        link.href = URL.createObjectURL(file);
        link.download = "dataref.json";
        link.click(); /* downloading the dataref.json */
        URL.revokeObjectURL(link.href);
        /* clearing fields and data */
        datarefs = []; /* clear the contents of dataref array */
        groups = []; /* clear the contents of group array */
        document.getElementById('result-list').innerHTML = ""
        document.getElementById('group-list').innerHTML = ""; // clear the group texterea
        /* reseting the form for another entries */ 
        close_alert_box();
        document.getElementById("checkme").checked = false;
        evaluate_checkbox();
        document.getElementById("result-list").disabled = true;
    }
    else
    {
        console.log("JSON is invalid");
        invalid_json(error_message);
    }
}
function isJSON(json_str) 
{
    let error_message = "???";
    let valid = true;
    try 
    {
        JSON.stringify(JSON.parse(json_str));
    } 
    catch (e) 
    {
        error_message = e.message
        valid = false;
    }
    return [valid,error_message];
}

function paste_dataref() 
{
    navigator.clipboard
        .readText()
        .then(
            cliptext =>
                (document.getElementById('dataref').value = cliptext),
            err => console.log(err)
        );
}
