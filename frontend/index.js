document.getElementById("displaytext").style.display = "none";

function searchPhoto() {
  var apigClient = apigClientFactory.newClient();

  var user_message = document.getElementById("note-textarea").value;
  console.log("Searching for:", user_message);

  var params = { q: user_message };
  var additionalParams = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  apigClient.searchGet(params, {}, additionalParams)
    .then(function (res) {
      var resp_data = res.data;
      console.log("Search response received:", resp_data);

      if (resp_data.imagePaths === "No Results found") {
        document.getElementById("displaytext").innerHTML = "Sorry could not find the image. Try another search words!";
        document.getElementById("displaytext").style.display = "block";
      } else {
        document.getElementById("img-container").innerHTML = "";
        resp_data.imagePaths.forEach(function (obj) {
          fetch(obj)
            .then((response) => {
              if (!response.ok) throw new Error("Network response was not ok");
              return response.text();
            })
            .then((base64String) => {
              const img = new Image();
              img.src = `data:image/jpeg;base64,${base64String}`;
              img.setAttribute("class", "banner-img");
              img.setAttribute("alt", "Uploaded Image");
              document.getElementById("img-container").appendChild(img);
            })
            .catch((error) => {
              console.error("Error fetching the image from S3:", error);
            });
        });
      }
    })
    .catch(function (error) {
      console.error("Error during search API call:", error);
    });
}

function handleFileUpload(event) {
  file = event.target.files[0];
  console.log("File selected:", file.name);
  document.querySelector(".upload_box header h4").innerText = file.name;
}

function submitPhotoAndLabel() {
  const file_input = document.getElementById("file_input");
  const custom_label = document.getElementById("custom_label").value;
  const upload_button = document.querySelector(".upload_box button");

  upload_button.innerText = "Uploading...";
  upload_button.style.backgroundColor = "#005af0";

  getBase64(file_input.files[0]).then((data) => {
    var apigClient = apigClientFactory.newClient();
    var body = data;
    var params = {
      object: file_input.files[0].name,
      'x-amz-meta-customLabels': custom_label,
      folder: "ass-b2"
    };

    var additionalParams = {
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": true,
      },
    };

    console.log("Initiating upload with parameters:", params);

    apigClient.uploadPut(params, body, additionalParams)
      .then(function (res) {
        console.log("Upload response:", res);
        if (res.status === 200) {
          upload_button.innerHTML = "Upload succeeded";
          upload_button.style.backgroundColor = "#499C55";
          console.log("Upload succeeded:", res.data);
        }
      })
      .catch((error) => {
        console.error("Upload failed with error:", error);
        upload_button.innerHTML = "Upload failed";
        upload_button.style.backgroundColor = "#F54234";
      });
  }).catch((error) => {
    console.error("Error preparing the file for upload:", error);
    upload_button.innerHTML = "Upload failed";
    upload_button.style.backgroundColor = "#F54234";
  });
}

function getBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      let encoded = reader.result.replace(/^data:(.*;base64,)?/, '');
      if (encoded.length % 4 > 0) {
        encoded += '='.repeat(4 - encoded.length % 4);
      }
      resolve(encoded);
    };
    reader.onerror = error => {
      console.error("Error reading file:", error);
      reject(error);
    };
  });
}
