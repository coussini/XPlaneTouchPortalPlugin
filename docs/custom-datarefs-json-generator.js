/*
    =============================================
    javascript for custom datarefs json generator
    =============================================

    This file is part of the XPlaneTouchPortalPLugin project.
    Copyright (c) XPlaneTouchPortalPlugin Developers/Contributors
    Copyright (C) 2024 Coussini
    All rights reserved.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

const oneId = 'xplane_plugin.';
const customDatarefJsonFileName = 'customDatarefJsonFile.json';
// arrays
let datarefs = [];
let groups = [];

// function on load
// validate form when the user press "add dataref to result" button
// when everything validated, save that to result box
(function () {
    'use strict';
    window.addEventListener('load', function () 
    {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        let formsThatNeedsValidation = document.getElementsByClassName('needs-validation');

        // This is a special treatment for an option choice according to the helper-description
        var selectElements = document.getElementsByClassName('helperDescription');

        // Add change event listener to each of the select elements
        Array.prototype.forEach.call(selectElements, function(selectElement) {
            selectElement.addEventListener('change', function() {
                var selectedOption = selectElement.options[selectElement.selectedIndex];
                var description = selectedOption.getAttribute('helper-description');
                document.getElementById('helperDescriptionText').innerHTML = description;
            });
            // Trigger the 'change' event immediately upon page load
            selectElement.dispatchEvent(new Event('change'));
        });

        // Loop over them and prevent submission
        let validation = Array.prototype.filter.call(formsThatNeedsValidation, function (form) 
        {
            try
            {
                form.addEventListener('submit', function (event) 
                {
                    if (form.checkValidity() === false) 
                    {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    form.classList.add('was-validated');
                    // If this form is valid, treat a dataref
                    if (form.checkValidity() === true) 
                    {
                        event.preventDefault();
                        insert_data_in_arrays();
                        // result list: for displaying datarefs and editing purposes
                        let resultList = document.querySelector('#result-list');
                        resultList.value = '\n' + JSON.stringify(datarefs, '\t', 2);
                        // group list: for displaying only
                        let groupList = document.querySelector('#group-list');
                        groupList.value = groups;
                        // enable check box button and result box
                        ['result-list','checkme'].forEach(enable_id);
                        // reseting the "left-form" form
                        form.reset();
                        // reseting the form validation
                        form.classList.remove('was-validated');
                    }
                }, false);
            }
            catch(error)
            {
                alert('catch an error: ' + error.message);
            }
        });
    }, false);
})();

// performing download_file function when the user press "saving to datarefs.json" button
// validate the result textarea (for JSON syntax and dataref value format)
// when everything validated, downloading result to 'datarefs.json' file
function download_file() 
{
    try
    {
        // disabling all input and select tag and select tag (for the "left-form")
        ['input','select'].forEach(disable_tag);
        // disabling all button (for the "left-form")
        ['paste','add-dataref'].forEach(disable_id);
        // validate the result textare for any JSON syntax
        let to_validate = document.getElementById('result-list').value;
        let [valid, error_message] = isJSON(to_validate);
        // when the result textare has good JSON syntax
        if (valid) 
        {
            // verify each dataref pattern are ok
            // the accepted pattern can be 'dataref_special/section' OR 'anotherDataref_special/section[index_number]'
            let object_json = JSON.parse(to_validate);
            for (let key in object_json)
            {
                let dataref = object_json[key].dataref;
                let result = dataref.match(/(^([a-zA-Z0-9 _\/.]+)\[(.*?)\]$)|(^([a-zA-Z0-9 _\/.]+)$)/);

                // does not match with the pattern
                if (result == null) 
                {
                    valid = false;
                    error_message = 'bad dataref value: ' + dataref;
                    invalid_json(error_message);
                    break;
                }
            }
        }
        // when everything are ok, downloading the result to the JSON file
        if (valid) 
        {
            downloading_result();
            // clearing fields and data
            datarefs = []; /* clear the contents of dataref array */
            groups = []; /* clear the contents of group array */
            document.getElementById('result-list').value = ''; // clear the result texterea
            document.getElementById('group-list').value = ''; // clear the group texterea
            // reseting the form for another entries
            close_alert_box();
            // enabling all input and select tag and select tag (for the "left-form") except the checkbox
            ['input','select'].forEach(enable_tag);
            // disable following id
            document.getElementById('checkme').checked = false;
            ['save','result-list','checkme'].forEach(disable_id);
            document.querySelector('#save').innerHTML = 'check me before saving';
            // enabling following id
            ['paste','add-dataref'].forEach(enable_id);
        }
        else 
        {
            invalid_json(error_message);
        }
    }
    catch(error)
    {
        alert('catch an error: ' + error.message);
    }
}

// disabling all corresponding tag
function disable_tag(tag)
{
    let tags = document.getElementsByTagName(tag);
    for (let j = 0; j < tags.length; j++) 
    {
        tags[j].disabled = true;
    }
}

// enabling all corresponding tag
function enable_tag(tag)
{
    let tags = document.getElementsByTagName(tag);
    for (let j = 0; j < tags.length; j++) 
    {
        tags[j].disabled = false;
    }
}

// disabling all corresponding id
function disable_id(id)
{
    document.getElementById(id).disabled = true;
}

// enabling all corresponding id
function enable_id(id)
{
    document.getElementById(id).disabled = false;
}

// inserting all fields from left form into an array
function insert_data_in_arrays() 
{
    // Prepare the object_dataref
    let dataref = document.getElementById('dataref').value;
    let id = oneId.concat(document.getElementById('dataref').value.replaceAll(' ', ''));
    let the_index = document.getElementById('index').value;
    let the_description = document.getElementById('desc').value;
    let group = document.getElementById('group').value;
    let comment = document.getElementById('comment').value;
    let TouchPortalFormat = document.getElementById('TouchPortalFormat').value;
    let UpdateMinimumValue = document.getElementById('UpdateMinimumValue').value;
    let UpdateMaximumValue = document.getElementById('UpdateMaximumValue').value;
    let AcceleratedControl = document.getElementById('AcceleratedControl').value;
    // If there's index entered, append it to the dataref name withing braket
    if (document.getElementById('index').value.length != 0) 
    {
        dataref = dataref.concat('[', the_index, ']');
        id = id.concat('[', the_index, ']');
        if  (group == 'Slider')
        {
            id = id.concat('_slider');
        }
    }
    // Else, check if the group is Command or Command_3 and put CMD or CMD_3 into braket respectively
    else
    {
        if (group == 'Command')
        {
            dataref = dataref.concat('[CMD]');
            id = id.concat('[CMD]');
        }
        else if  (group == 'Command_3')
        {
            dataref = dataref.concat('[CMD_3]');
            id = id.concat('[CMD_3]');
        }
        // Else, check if the group is Slider (concat 'slider' toi the id)
        else if  (group == 'Slider')
        {
            id = id.concat('_slider');
        }
        else 
        {
        } 
    }
    let objet_dataref =
    {
        id: id,
        desc: the_description,
        group: group,
        dataref: dataref,
        comment: comment,
        touch_portal_format: TouchPortalFormat,
        xplane_update_min_value: UpdateMinimumValue,
        xplane_update_max_value: UpdateMaximumValue,
        accelerated_control: AcceleratedControl
    };
    // save the objet_dataref
    datarefs.push(objet_dataref);
    // keep unic group name only
    let elementExists = groups.includes(group);
    if (!elementExists) 
    {
        groups.push(group);
    }
}

// downloading the result to json file
function downloading_result()
{
    let begin = '{\n"datarefs": '
    let middle = document.getElementById('result-list').value;
    let end = '\n}';
    let content = begin.concat(middle).concat(end);
    let file = new Blob([content], { type: 'text/plain' });
    // prepare a link for the download file
    let link = document.createElement('a');
    link.href = URL.createObjectURL(file);
    link.download = customDatarefJsonFileName;
    // downloading the datarefs.json
    link.click(); 
    URL.revokeObjectURL(link.href);
}

// toogle button 'saving to datarefs.json' vs 'check me before saving' 
function evaluate_checkbox() 
{
    if (document.getElementById('checkme').checked) 
    {
        document.querySelector('#save').innerHTML = 'saving to datarefs.json';
        document.getElementById('save').disabled = false;
    }
    else 
    {
        document.querySelector('#save').innerHTML = 'check me before saving';
        document.getElementById('save').disabled = true;
    }
}

// give message to alert box for some JSON value and syntax
function invalid_json(message) 
{
    document.getElementById('alert-message').innerHTML = message;
    const alert = document.getElementById('danger-alert');
    alert.style.display = 'block';
}

// removing message in alert box and hide the alert box
function close_alert_box() 
{
    document.getElementById('alert-message').innerHTML = '';
    const alert = document.getElementById('danger-alert');
    alert.style.display = 'none';
}

// validate JSON string for syntax
function isJSON(json_str) {
    let error_message = '???';
    let valid = true;
    try {
        JSON.stringify(JSON.parse(json_str));
    }
    catch (e) {
        error_message = e.message;
        valid = false;
    }
    return [valid, error_message];
}

// paste contents from clipboard
function paste_dataref() {
    navigator.clipboard
        .readText()
        .then(
            cliptext =>
                (document.getElementById('dataref').value = cliptext),
            err => alert(err)
        );
}
