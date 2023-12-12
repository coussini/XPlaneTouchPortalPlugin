/*
This Jquery and javascript script generate the Touch Portal JSON file for X-Plane
Only for Chrome
*/

$.fn.formToJSON = function () {
    var out = {};

    var cleanValue = function ($f) {
        var v = $f.val() || "";
        // clean values?
        return v;
    }

    var pushValue = function (o, id, v) {
        if (o[id] != null) {
            if (!o[id].push) {
                o[id] = [o[id]];
            }
            o[id].push(v);
        } else {
            o[id] = v;
        }
    }

    var pushLevel = function (o, list, v) {
        var id = list.shift();
        if (list.length == 0) {
            pushValue(o, id, v)
        } else {
            if (o[id] == null) {
                o[id] = {}; 
            }
            pushLevel(o[id], list, v)
        }
    }

    this.each(function (i, f) {
        var v = cleanValue($(f));
        var idList = f.id.replace(/:\d*/g, "").split(".");
        pushLevel(out, idList, v);
    });
    
    return out;
};             
var isValidElement = function isValidElement(element) {
  return element.name && element.value;
};

/**
 * Checks if an element’s value can be saved (e.g. not an unselected checkbox).
 * @param  {Element} element  the element to check
 * @return {Boolean}          true if the value should be added, false if not
 */
var isValidValue = function isValidValue(element) {
  return !['checkbox', 'radio'].includes(element.type) || element.checked;
};

/**
 * Checks if an input is a checkbox, because checkboxes allow multiple values.
 * @param  {Element} element  the element to check
 * @return {Boolean}          true if the element is a checkbox, false if not
 */
var isCheckbox = function isCheckbox(element) {
  return element.type === 'checkbox';
};

/**
 * Checks if an input is a `select` with the `multiple` attribute.
 * @param  {Element} element  the element to check
 * @return {Boolean}          true if the element is a multiselect, false if not
 */
var isMultiSelect = function isMultiSelect(element) {
  return element.options && element.multiple;
};

/**
 * Retrieves the selected options from a multi-select as an array.
 * @param  {HTMLOptionsCollection} options  the options for the select
 * @return {Array}                          an array of selected option values
 */
var getSelectValues = function getSelectValues(options) {
  return [].reduce.call(options, function (values, option) {
    return option.selected ? values.concat(option.value) : values;
  }, []);
};

/**
 * A more verbose implementation of `formToJSON()` to explain how it works.
 *
 * NOTE: This function is unused, and is only here for the purpose of explaining how
 * reducing form elements works.
 *
 * @param  {HTMLFormControlsCollection} elements  the form elements
 * @return {Object}                               form data as an object literal
 */
var formToJSON_deconstructed = function formToJSON_deconstructed(elements) {

  // This is the function that is called on each element of the array.
  var reducerFunction = function reducerFunction(data, element) {

    // Add the current field to the object.
    data[element.name] = element.value;

    // For the demo only: show each step in the reducer’s progress.
    console.log(JSON.stringify(data));

    return data;
  };

  // This is used as the initial value of `data` in `reducerFunction()`.
  var reducerInitialValue = {};

  // To help visualize what happens, log the inital value, which we know is `{}`.
  console.log('Initial `data` value:', JSON.stringify(reducerInitialValue));

  // Now we reduce by `call`-ing `Array.prototype.reduce()` on `elements`.
  var formData = [].reduce.call(elements, reducerFunction, reducerInitialValue);

  // The result is then returned for use elsewhere.
  return formData;
};

/**
 * Retrieves input data from a form and returns it as a JSON object.
 * @param  {HTMLFormControlsCollection} elements  the form elements
 * @return {Object}                               form data as an object literal
 */
var formToJSON = function formToJSON(elements) {
  return [].reduce.call(elements, function (data, element) {

    // Make sure the element has the required properties and should be added.
    if (isValidElement(element) && isValidValue(element)) {

      /*
       * Some fields allow for more than one value, so we need to check if this
       * is one of those fields and, if so, store the values as an array.
       */
      if (isCheckbox(element)) {
        data[element.name] = (data[element.name] || []).concat(element.value);
      } else if (isMultiSelect(element)) {
        data[element.name] = getSelectValues(element);
      } else {
        data[element.name] = element.value;
      }
    }

    return data;
  }, {});
};

/**
 * A handler function to prevent default submission and run our custom script.
 * @param  {Event} event  the submit event triggered by the user
 * @return {void}
 */
var handleFormSubmit = function handleFormSubmit(event) {

  // Stop the form from submitting since we’re handling that with AJAX.
  event.preventDefault();

  // Call our function to get the form data.
  var data = formToJSON(form.elements);
  var $fields = $("input:text").not("[name^='__']");
  var data = $fields.formToJSON();
  
  //alert("hi download qa.txt file");

  // Demo only: print the form data onscreen as a formatted JSON object.
  var dataContainer = document.getElementsByClassName('results__display')[0];

  // Use `JSON.stringify()` to make the output valid, human-readable JSON.
  dataContainer.textContent = JSON.stringify(data, null, "  ");

  // ...this is where we’d actually do something with the form data...
  downloadInnerHtml(fileName, 'JsonCompiled','text/html');
};

/*
 * This is where things actually get started. We find the form element using
 * its class name, then attach the `handleFormSubmit()` function to the 
 * `submit` event.
 */
var form = document.getElementsByClassName('contact-form')[0];
form.addEventListener('submit', handleFormSubmit);

function downloadInnerHtml(filename, elId, mimeType) {
    var elHtml = document.getElementById(elId).innerHTML;
    var link = document.createElement('a');
    mimeType = mimeType || 'text/plain';

    link.setAttribute('download', filename);
    link.setAttribute('href', 'data:' + mimeType + ';charset=utf-8,' + encodeURIComponent(elHtml));
    link.click(); 
}

var fileName =  'qa.txt'; // You can use the .txt extension if you want

$('#downloadLink').click(function(){
    downloadInnerHtml(fileName, 'JsonCompiled','text/html');
});
qn = 0;
$('#addqa').click(function(){
  qn++;
  // alert('addqa');
  var iData ='<br>'+qn+'<input type="text" id="a'+qn+'.q" value="題目" />   <input type="text" id="a'+qn+'.q1" value="xx" />    <input type="text" id="a'+qn+'.q2" value="xx" />    <input type="text" id="a'+qn+'.q3" value="xx" />    <input type="text" id="a'+qn+'.q4" value="xx" />    <input type="text" id="a'+qn+'.corr" value="3" /><input type="text" id="a'+qn+'.answer" value="answer_describe" />';
  $('#insert').append(iData);
});