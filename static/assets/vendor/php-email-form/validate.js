/**
 * PHP Email Form Validation - v3.9
 * URL: https://bootstrapmade.com/php-email-form/
 * Author: BootstrapMade.com
 */
(function () {
    "use strict";

    let forms = document.querySelectorAll('.php-email-form');

    forms.forEach(function (e) {
        e.addEventListener('submit', function (event) {
            event.preventDefault();

            let thisForm = this;

            let action = thisForm.getAttribute('action');

            if (!action) {
                displayError(thisForm, 'The form action property is not set!');
                return;
            }
            thisForm.querySelector('.loading').classList.add('d-block');
            thisForm.querySelector('.error-message').classList.remove('d-block');
            thisForm.querySelector('.sent-message').classList.remove('d-block');

            let formData = new FormData(thisForm);

            php_email_form_submit(thisForm, action, formData);
        });
    });

    function php_email_form_submit(thisForm, action, formData) {
        const csrfToken = formData.get('csrfmiddlewaretoken');
        fetch(action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(`${errorData.message}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                thisForm.querySelector('.loading').classList.remove('d-block');
                thisForm.querySelector('.sent-message').classList.add('d-block');
                thisForm.reset();

            })
            .catch(error => {
                let errorMessage = "Límite de envío superado, inténtelo de nuevo más tarde.";
                displayError(thisForm, errorMessage);

            });
    }

    function displayError(thisForm, error) {
        thisForm.querySelector('.loading').classList.remove('d-block');
        thisForm.querySelector('.error-message').innerHTML = error;
        thisForm.querySelector('.error-message').classList.add('d-block');
    }

})();
