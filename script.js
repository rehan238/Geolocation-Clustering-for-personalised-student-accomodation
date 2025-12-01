function populateColleges() {
  const city = document.getElementById("city").value;
  const collegeDropdown = document.getElementById("college");
  collegeDropdown.innerHTML = '<option value="">Select College</option>'; // Clear previous options

  if (city && cityColleges[city]) {
      cityColleges[city].forEach(college => {
          const option = document.createElement("option");
          option.value = `${college.lat},${college.lng}`;
          option.textContent = college.name;
          collegeDropdown.appendChild(option);
      });
  }
}

function updateMap() {
  const college = document.getElementById("college").value;
  if (college) {
      const [lat, lng] = college.split(",");
      const map = document.getElementById("map");
      map.src = `https://maps.google.com/maps?q=${lat},${lng}&z=15&output=embed`;
  }
}
function updateMapFromLatLng() {
  const latitude = document.getElementById("latitude").value;
  const longitude = document.getElementById("longitude").value;

  if (latitude && longitude) {
      const map = document.getElementById("map");
      map.src = `https://maps.google.com/maps?q=${latitude},${longitude}&z=15&output=embed`;
  } else {
      alert("Please enter both latitude and longitude to preview the map.");
  }
}

function toggleInputFields() {
  const inputMethod = document.getElementById("input-method").value;
  const latLngFields = document.getElementById("lat-lng-fields");
  const cityCollegeFields = document.getElementById("city-college-fields");

  if (inputMethod === "lat-lng") {
      latLngFields.style.display = "block";
      cityCollegeFields.style.display = "none";
  } else if (inputMethod === "city-college") {
      latLngFields.style.display = "none";
      cityCollegeFields.style.display = "block";
  } else {
      latLngFields.style.display = "none";
      cityCollegeFields.style.display = "none";
  }
}

document.getElementById('location-form').onsubmit = async (e) => {
  e.preventDefault();

  const inputMethod = document.getElementById("input-method").value;
  let latitude, longitude;

  if (inputMethod === "lat-lng") {
      latitude = document.getElementById("latitude").value;
      longitude = document.getElementById("longitude").value;
  } else if (inputMethod === "city-college") {
      const college = document.getElementById("college").value;
      if (!college) {
          alert("Please select a college.");
          return;
      }
      [latitude, longitude] = college.split(",");
  }

  const preference1 = document.getElementById('preference1').value;
  const preference2 = document.getElementById('preference2').value;
  const display_metro = document.getElementById('display-metro').value; // Get the value of the hidden input

  if (!latitude || !longitude) {
      alert("Please provide valid latitude and longitude.");
      return;
  }

  try {
      const response = await fetch('/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
              latitude: latitude,
              longitude: longitude,
              preference1: preference1,
              preference2: preference2,
              display_metro: display_metro, // Include display_metro
          }),
      });

      if (response.ok) {
          const result = await response.json();
          if (result.status === 'success') {
              document.getElementById('map').src = `/map`;
              alert('Map generated successfully');
          } else {
              alert(result.message || 'Error generating map');
          }
      } else {
          alert('Error: Could not fetch data');
      }
  } catch (error) {
      alert('Error: Something went wrong');
      console.error(error);
  }
};




// When 'Yes' button is clicked
document.getElementById("metro-yes").addEventListener("click", function () {
  const metroValue = this.getAttribute("data-value"); // Get the 'data-value' of the clicked button

  document.getElementById("display-metro").value = metroValue; // Update hidden input value
  this.classList.add("active"); // Highlight the selected button
  document.getElementById("metro-no").classList.remove("active"); // Remove highlight from the other button
});

// When 'No' button is clicked
document.getElementById("metro-no").addEventListener("click", function () {
  const metroValue = this.getAttribute("data-value"); // Get the 'data-value' of the clicked button

  document.getElementById("display-metro").value = metroValue; // Update hidden input value
  this.classList.add("active"); // Highlight the selected button
  document.getElementById("metro-yes").classList.remove("active"); // Remove highlight from the other button
});