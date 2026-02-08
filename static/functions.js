function autocompleteCard()
{
    var autocompleteList = document.getElementById("autocompleteValues");

    var cardName = document.getElementById("cardName");

    var xhttp = new XMLHttpRequest();
    
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
          var response = this.responseText;
          if (response == '') {
            while (autocompleteList.hasChildNodes()) {
              autocompleteList.removeChild(autocompleteList.firstChild);
            }
            autocompleteList.innerHTML = "...";
            return;
          }
          var cardData = JSON.parse(response);

          while (autocompleteList.hasChildNodes()) {
            autocompleteList.removeChild(autocompleteList.firstChild);
          }

          for (let i = 0; i < cardData.length; i++) {
            var cardInfo = cardData[i];
            var autocompleteRow = document.createElement("li");
            var manaCostContainer = document.createElement("div");
            manaCostContainer.innerText = cardInfo.mana_cost;
            manaCostContainer.classList.add("mana-cost");
            autocompleteRow.appendChild(manaCostContainer);
            var cardLink = document.createElement("a");
            cardLink.href = "cards?name=" + cardInfo.name;
            cardLink.innerHTML += cardInfo.name;
            autocompleteRow.appendChild(cardLink);

            var autocompleteImage = document.createElement("img");
            autocompleteImage.src = cardInfo.image_uris.normal;
            autocompleteImage.alt = cardInfo.name;
            autocompleteImage.classList.add("autocompleteImg");
            autocompleteList.appendChild(autocompleteRow);
            autocompleteRow.appendChild(autocompleteImage);
          }
          textToMana();
        }
      };
    xhttp.open("POST", "autocomplete", true);
    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhttp.send("cardName="+cardName.value);
}

function sort()
{
  var sortValue = document.getElementById("sorter").value;
  var url = new URL(window.location.href);
  url.searchParams.set("sort", sortValue);
  console.log(url);
  window.location.href = url.toString();
}

function changeOrder()
{
  console.log("Order change");
  var url = new URL(window.location.href);
  var urlParams = new URLSearchParams(window.location.search);
  const dir = urlParams.get('dir');
  if (! dir | dir == "asc")
  {
    url.searchParams.set("dir", "desc");
  }
  else
  {
    url.searchParams.set("dir", "asc");
  }

  window.location.href = url.toString();
}

function setSelectValue(sortValue)
{
  var sorter = document.getElementById("sorter");
  sorter.value = sortValue;
}

function textToMana()
{
  const manaCosts = document.getElementsByClassName("mana-cost");
  for (const manaCost of manaCosts)
  {
    const text = manaCost.innerText;
    manaCost.innerText = "";
    symbols = text.split("{");
    for (let symbol of symbols.slice(1))
    {
      symbol = symbol.slice(0,-1);
      let manaSymbol = document.createElement("i");
      manaSymbol.classList.add("ms", "ms-cost", "ms-shadow");
      if (symbol.length == 1)
      {
        manaSymbol.classList.add("ms-" + symbol[0].toLowerCase());
      }
      if (symbol.length == 3)
      {
        let classes = symbol.split("/")
        if ("P" in classes)
        {
          manaSymbol.classList.add("ms-h")
          manaSymbol.classList.add("ms-" + classes[0].toLowerCase());
        }
        else
        {
          manaSymbol.classList.add("ms-" + classes[0].toLowerCase()+classes[1].toLowerCase());
        }
      }
      manaCost.appendChild(manaSymbol);
    }
  }
}

function changeFormat()
{
  const urlParams = new URLSearchParams(window.location.search);
  const deckName = urlParams.get('name'); 
  var format = document.getElementById("change-format").value;
  console.log(format);
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      response = JSON.parse(this.responseText);
      showMessage(response["message"], response["type"])
    }
  }
  xhttp.open("POST", "changeFormat", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("format="+format+"&deckName="+deckName);
}

function openEdit()
{
  var deckNameContainer = document.getElementById("deck-name-container");
  var deckNameHeader = document.getElementById("deck-name");
  var editImage = document.getElementById("edit-image");

  editImage.style.display = "none";
  var newText = document.createElement("input");
  newText.type = "text";
  newText.id = "name-changer";
  newText.value = deckNameHeader.innerText;
  
  deckNameHeader.style.display = "none";
  deckNameContainer.appendChild(newText);

  var submitButton = document.createElement("button");
  submitButton.type = "submit";
  submitButton.id = "submit-name";
  submitButton.innerText = "Submit!"
  submitButton.addEventListener("click", changeName)
  deckNameContainer.appendChild(submitButton);
}

function changeName() {
  var newName = document.getElementById("name-changer").value;
  const urlParams = new URLSearchParams(window.location.search);
  const deckName = urlParams.get('name'); 
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      window.location.href = '/deck?name=' + newName;
    }
  }
  xhttp.open("POST", "changeName", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("newName="+newName+"&deckName="+deckName);
}

function exportToArena() {
  const urlParams = new URLSearchParams(window.location.search);
  const deckName = urlParams.get('name'); 
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      response = JSON.parse(this.responseText);
      console.log(response)
      showMessage(response["message"], response["type"]);
      navigator.clipboard.writeText(response["exportString"]);
    }
  }
  xhttp.open("POST", "exportToArena", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("deckName="+deckName);
}

function showMessage(message, type) {
  var messageContainer = document.createElement("div");
  messageContainer.classList.add("alert", "alert-"+type, "alert-dismissible");
  var closeButton = document.createElement("a");

  closeButton.href="#";
  closeButton.classList.add("close");
  closeButton.innerText="\u00D7";
  closeButton.setAttribute("data-dismiss", "alert");
  closeButton.setAttribute("aria-label", "close");
  messageContainer.innerText=message;
  messageContainer.appendChild(closeButton);

  var content = document.getElementById("content");
  content.insertBefore(messageContainer, content.firstChild);
}