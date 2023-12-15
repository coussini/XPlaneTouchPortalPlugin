const oneId = 'XPlanePlugin.';
let datarefs = [];
let group_array = [];

/* function on load */
/* validate form when the user press "add dataref to result" button */
/* when everything validated, save that to result box */
(function () {
    'use strict';
    window.addEventListener('load', function () 
    {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        let formsThatNeedsValidation = document.getElementsByClassName('needs-validation');
        // Loop over them and prevent submission
        let validation = Array.prototype.filter.call(formsThatNeedsValidation, function (form) 
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
                if(form.checkValidity() === true)
                {
                    event.preventDefault();
                    let dataref = document.getElementById('dataref').value;
                    let the_index = document.getElementById('index').value;
                    let group = document.getElementById('group').value;
                    // If there's index entered, append it to the dataref name withing braket
                    if (document.getElementById('index').value.length != 0)
                    {
                        dataref = dataref.concat("[", the_index, "]");
                    }
                    let objet_dataref = 
                    {
                        id: oneId.concat(document.getElementById('desc').value.replaceAll(' ','')),
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
                    let elementExists = group_array.includes(group);
                    if (!elementExists) 
                    {
                        group_array.push(group);
                    }
                    // result list: for displaying datarefs and editing purposes
                    let resultList = document.querySelector('#result-list');
                    resultList.textContent = '\n' + JSON.stringify(datarefs, '\t', 2);
                    // group list: for displaying only
                    let groupList = document.querySelector('#group-list');
                    groupList.textContent = group_array;
                    // saving to localStorage
                    localStorage.setItem('MyDatarefList', JSON.stringify(datarefs) );
                    // enable check box button and result box
                    document.getElementById("result-list").disabled  = false;
                    document.getElementById("checkme").disabled  = false;
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
  if (document.getElementById('checkme').checked) {
      document.querySelector('#save').innerHTML = 'saving to dataref.json';
      document.getElementById('save').disabled = false;
  }
  else 
  {
      document.querySelector('#save').innerHTML = 'check me before saving';
      document.getElementById('save').disabled = true;
  }
}

function downloadFile()
{
  let link = document.createElement("a");
  let begin = '{\n"datarefs": '
  let middle = document.getElementById('result-list').value;
  let end = '\n}';
  let content = begin.concat(middle).concat(end); 
  console.log(JSON.stringify(content));
  let file = new Blob([content], { type: 'text/plain' });
  link.href = URL.createObjectURL(file);
  link.download = "dataref.json";
  link.click();
  URL.revokeObjectURL(link.href);
  document.getElementById('result-list').value = ""; // to clear the texterea for the pass
}

