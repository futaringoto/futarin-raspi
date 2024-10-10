const formEl = document.getElementById("settingForm");
const submitButtonEl = document.getElementById("submitButton");
const certainEl = document.getElementById("certain");
const successMsgEl = document.getElementById("successMsg");
const errorMsgEl = document.getElementById("errorMsg");

submitButtonEl.addEventListener(
  "click",
  () => {
    const formData = new FormData(formEl);
    const action = formEl.action;
    const options = {
      method: "POST",
      body: formData,
    };

    fetch(action, options).then((e) => {
      if (e.status === 200) {
        certainEl.classList.remove("invisible");
        successMsgEl.classList.remove("invisible");
      } else {
        errorMsgEl.classList.remove("invisible");
        setTimeout(() => {
          errorMsgEl.classList.add("invisible");
        }, 6000);
      }
    });
  },
  false,
);
