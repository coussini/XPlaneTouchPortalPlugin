let datarefs = [];
let group_array = [];
let oneId = 'XPlanePlugin.';
let firstTime = true;

function validate_form()
{
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation')
    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
    .forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            form.classList.add('was-validated')
        }, false)
    })
}

function add_dataref()
{
    var inpObj = document.getElementById("json-form");
    if (inpObj.checkValidity() == false) {
        return false;
    }
    else 
    {
        let dataref_with_index = document.getElementById('dataref').value;
        if (document.getElementById('index').value.length != 0)
        {
            the_index = document.getElementById('index').value;
            op_brak = "[";
            cl_brak = "]";
            dataref_with_index = dataref_with_index.concat(op_brak, the_index, cl_brak);
        }
        let objet_dataref = {
            id: oneId.concat(document.getElementById('desc').value.replaceAll(' ','')),
            desc: document.getElementById('desc').value,
            group: document.getElementById('group').value,
            type: document.getElementById('type').value,
            value: document.getElementById('value').value,
            dataref: dataref_with_index,
            comment: document.getElementById('comment').value
        };
        // sauvegarder object datarefs
        datarefs.push(objet_dataref);
        // sauvegarder les groupes unique seulement
        gr = document.getElementById('group').value;
        const elementExists = group_array.includes(gr);
        if (!elementExists) {
            group_array.push(gr);
        }
        document.forms[0].reset(); // to clear the form for the next entries
        //for display and editing purposes
        let msg = document.querySelector('#msg');
        msg.textContent = '\n' + JSON.stringify(datarefs, '\t', 2);
        //for display only
        let gl = document.querySelector('#group-list');
        gl.textContent = group_array;
        //for display and editing purposes
        //saving to localStorage
        localStorage.setItem('MyDatarefList', JSON.stringify(datarefs) );
        document.getElementById("msg").disabled  = false;
        document.getElementById("checkme").disabled  = false;
    }
}

function evaluate_checkbox()
{
  if (document.getElementById('checkme').checked) {
      document.querySelector('#save').innerHTML = 'saving to dataref.json';
      document.getElementById('save').disabled = false;
  }
  else {
      document.querySelector('#save').innerHTML = 'check me before saving';
      document.getElementById('save').disabled = true;
  }
}

function downloadFile()
{
  const link = document.createElement("a");
  const begin = '{\n"datarefs": '
  const middle = document.getElementById('msg').value;
  const end = '\n}';
  const content = begin.concat(middle).concat(end); 
  console.log(JSON.stringify(content));
  const file = new Blob([content], { type: 'text/plain' });
  link.href = URL.createObjectURL(file);
  link.download = "dataref.json";
  link.click();
  URL.revokeObjectURL(link.href);
  document.getElementById('msg').value = ""; // to clear the texterea for the pass
}

