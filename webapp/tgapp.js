const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const itemsContainer = document.getElementById("items");
const submitBtn = document.getElementById("submitBtn");
const noteInput = document.getElementById("note");

const selectedItems = new Map();

function getUserName() {
  const user = tg.initDataUnsafe?.user;
  if (!user) return "Неизвестный пользователь";
  return [user.first_name, user.last_name].filter(Boolean).join(" ");
}

function toggleItem(item, card) {
  if (selectedItems.has(item.id)) {
    selectedItems.delete(item.id);
    card.classList.remove("selected");
  } else {
    selectedItems.set(item.id, {
      id: item.id,
      title: item.title,
      place: item.place
    });
    card.classList.add("selected");
  }
}

function createCard(item) {
  const card = document.createElement("article");
  card.className = "card";

  card.innerHTML = `
    <img class="card-image" src="${item.image}" alt="${item.title}">
    <div class="card-body">
      <h2 class="card-title">${item.title}</h2>
      <p class="card-place">${item.place}</p>
      <button class="card-toggle" type="button">Выбрать</button>
    </div>
  `;

  const button = card.querySelector(".card-toggle");
  button.addEventListener("click", () => {
    toggleItem(item, card);
    button.textContent = selectedItems.has(item.id) ? "Выбрано 💖" : "Выбрать";
  });

  return card;
}

async function loadItems() {
  const response = await fetch("./items.json");
  const items = await response.json();
  items.forEach((item) => {
    itemsContainer.appendChild(createCard(item));
  });
}

submitBtn.addEventListener("click", () => {
  const items = Array.from(selectedItems.values());

  if (!items.length) {
    tg.showAlert("Выбери хотя бы одну позицию 💕");
    return;
  }

  const payload = {
    user_name: getUserName(),
    note: noteInput.value.trim(),
    items: items
  };

  tg.sendData(JSON.stringify(payload));
});

loadItems().catch((error) => {
  console.error(error);
  tg.showAlert("Не удалось загрузить карточки");
});
