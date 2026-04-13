/* ============================================================
   SEASON CONFIG
   ============================================================ */
const SEASON_STYLE = {
  spring: { bg: '#acffbf', color: '#2d6a4f', label: 'Spring' },
  summer: { bg: '#ffeba9', color: '#856404', label: 'Summer' },
  autumn: { bg: '#ffbf8f', color: '#8b3a1a', label: 'Autumn' },
  winter: { bg: '#abdcff', color: '#154360', label: 'Winter' },
};

/* ============================================================
   FILTER STATE
   ============================================================ */
let selectedSeasons     = new Set();
let requiredIngredients = new Set(); // ingredient name strings, lowercase
let allRecipes = [];

function normalizeTag(tag) {
  return tag.replace(/\s+/g, '').toLowerCase();
}

function normalizeSet(tagSet) {
  return [...tagSet].map(t => t.replace(/\s+/g, '').toLowerCase());
}

/* ============================================================
   RENDER CARDS
   ============================================================ */
function renderCards(recipes) {
  const grid = document.getElementById('recipesGrid');
  const normSeasons = normalizeSet(selectedSeasons);

  const filtered = recipes
    .filter(r => {
      // Season filter
      if (normSeasons.length && !normSeasons.includes(normalizeTag(r.season))) return false;

      // Ingredient filter — recipe must contain ALL required ingredients
      if (requiredIngredients.size > 0) {
        const recipeIngNames = (r.ingredients || []).map(i => i.name.toLowerCase());
        for (const req of requiredIngredients) {
          // partial match: "tom" matches "tomatoes"
          if (!recipeIngNames.some(name => name.includes(req))) return false;
        }
      }

      return true;
    })
    .sort((a, b) => b.score - a.score);

  if (filtered.length === 0) {
    grid.innerHTML = '<p class="no-results">No recipes match the selected filters.</p>';
    return;
  }

  grid.innerHTML = filtered.map(r => {
    const season = SEASON_STYLE[r.season];
    const allTags = [...(r.field || []), ...(r.lang || []), ...(r.simreal || [])];

    const imageBlock = r.image
      ? `<img src="${r.image}" alt="${r.title}" class="recipe-image" />`
      : `<div class="recipe-season-block" style="background:${season.bg}">
           <span class="season-label" style="color:${season.color}">${season.label}</span>
         </div>`;

    const stars = '★'.repeat(r.score) + '☆'.repeat(5 - r.score);

    return `
      <div class="recipe-card"
           data-recipe="${r.id}"
           data-season="${r.season}"
           style="background-color:${season.bg}">
        <div class="card-top">
          ${imageBlock}
          <h3>${r.title}</h3>
          <p>${r.desc}</p>
        </div>
        <div class="card-bottom">
          <div class="tags">
            ${allTags.map(t => `<span class="tag">${t}</span>`).join('')}
          </div>
          <div class="card-score" title="Score: ${r.score}/5">${stars}</div>
        </div>
      </div>`;
  }).join('');

  attachCardListeners();
}

/* ============================================================
   INGREDIENT SEARCH
   ============================================================ */
function renderIngredientTags() {
  const container = document.getElementById('ingredientTags');
  container.innerHTML = [...requiredIngredients].map(ing => `
    <span class="ingredient-tag">
      ${ing}
      <button class="ingredient-tag-remove" data-ing="${ing}" title="Remove">✕</button>
    </span>
  `).join('');

  container.querySelectorAll('.ingredient-tag-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      requiredIngredients.delete(btn.dataset.ing);
      renderIngredientTags();
      renderCards(allRecipes);
    });
  });
}

function addIngredient(value) {
  const trimmed = value.trim().toLowerCase();
  if (!trimmed) return;
  requiredIngredients.add(trimmed);
  renderIngredientTags();
  renderCards(allRecipes);
}

function setupIngredientSearch() {
  const input  = document.getElementById('ingredientInput');
  const addBtn = document.getElementById('ingredientAddBtn');

  addBtn.addEventListener('click', () => {
    addIngredient(input.value);
    input.value = '';
    input.focus();
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addIngredient(input.value);
      input.value = '';
    }
    // Backspace on empty input removes last tag
    if (e.key === 'Backspace' && input.value === '' && requiredIngredients.size > 0) {
      const last = [...requiredIngredients].at(-1);
      requiredIngredients.delete(last);
      renderIngredientTags();
      renderCards(allRecipes);
    }
  });
}

/* ============================================================
   MODAL
   ============================================================ */
function formatQuantity(qty) {
  if (Number.isInteger(qty)) return String(qty);
  return parseFloat(qty.toFixed(2)).toString();
}

function renderIngredients(ingredients, servings, baseServings) {
  return ingredients.map(i => {
    const scaled = (i.quantity * servings) / baseServings;
    return `<li>
      <span class="ing-qty">${formatQuantity(scaled)}</span>
      <span class="ing-unit">${i.unit}</span>
      <span class="ing-name">${i.name}</span>
    </li>`;
  }).join('');
}

function buildModalHtml(r) {
  const season = SEASON_STYLE[r.season];
  const allTags = [...(r.field || []), ...(r.lang || []), ...(r.simreal || [])];
  const baseServings = r.number_servings || 1;

  const imageHtml = r.image
    ? `<div class="modal-image"><img src="${r.image}" alt="${r.title}" /></div>`
    : '';

  const ingredientsHtml = r.ingredients && r.ingredients.length
    ? `<div class="modal-section">
        <div class="section-header">
          <h3 class="section-title">Ingredients</h3>
          <div class="servings-control">
            <button class="servings-btn" id="servings-down">−</button>
            <span class="servings-display">
              <span id="servings-count">${baseServings}</span> servings
            </span>
            <button class="servings-btn" id="servings-up">+</button>
          </div>
        </div>
        <ul class="ingredients-list" id="ingredients-list">
          ${renderIngredients(r.ingredients, baseServings, baseServings)}
        </ul>
       </div>`
    : '';

  const stepsHtml = r.steps && r.steps.length
    ? `<div class="modal-section">
        <h3 class="section-title">Steps</h3>
        <ol class="steps-list">
          ${r.steps.map((s, i) => `<li><span class="step-num">${i + 1}</span><span>${s}</span></li>`).join('')}
        </ol>
       </div>`
    : '';

  return `
    <div class="modal" style="display:flex">
      <div class="modal-content">
        <button class="close-btn mobile-only">✕</button>
        ${imageHtml}
        <div class="modal-header">
          <div class="title">${r.title}</div>
          <div class="modal-meta">
            <span class="season-pill" style="background:${season.bg};color:${season.color}">${season.label}</span>
            <span class="score-pill">${'★'.repeat(r.score)}${'☆'.repeat(5 - r.score)}</span>
          </div>
        </div>
        <div class="tags">${allTags.map(t => `<span class="tag">${t}</span>`).join('')}</div>
        <div class="modal-divider"></div>
        ${ingredientsHtml}
        ${stepsHtml}
      </div>
    </div>`;
}

function attachCardListeners() {
  const container = document.getElementById('modal-container');

  document.querySelectorAll('.recipe-card').forEach(card => {
    card.addEventListener('click', () => {
      const recipeId = card.dataset.recipe;
      const recipe = allRecipes.find(r => r.id === recipeId);
      if (!recipe) return;

      container.innerHTML = buildModalHtml(recipe);

      const modal = container.querySelector('.modal');
      const closeBtn = modal.querySelector('.close-btn');
      if (closeBtn) closeBtn.addEventListener('click', () => { modal.style.display = 'none'; });

      const baseServings = recipe.number_servings || 1;
      const countEl = modal.querySelector('#servings-count');
      const listEl  = modal.querySelector('#ingredients-list');

      if (countEl && listEl) {
        let current = baseServings;

        modal.querySelector('#servings-up').addEventListener('click', () => {
          current++;
          countEl.textContent = current;
          listEl.innerHTML = renderIngredients(recipe.ingredients, current, baseServings);
        });

        modal.querySelector('#servings-down').addEventListener('click', () => {
          if (current <= 1) return;
          current--;
          countEl.textContent = current;
          listEl.innerHTML = renderIngredients(recipe.ingredients, current, baseServings);
        });
      }
    });
  });

  window.addEventListener('click', (e) => {
    const modal = container.querySelector('.modal');
    if (modal && e.target === modal) modal.style.display = 'none';
  });
}

window.closeModal = function () {
  const modal = document.querySelector('#modal-container .modal');
  if (modal) modal.style.display = 'none';
};

/* ============================================================
   SEASON FILTER
   ============================================================ */
function setupFilterGroup(groupId, tagSet, recipes) {
  document.querySelectorAll(`#${groupId} .filter-tag`).forEach(tag => {
    tag.addEventListener('click', () => {
      const val = tag.dataset.tag;
      const isActive = tag.classList.toggle('active');
      if (isActive) tagSet.add(val);
      else tagSet.delete(val);
      renderCards(recipes);
    });
  });
}

/* ============================================================
   NAVBAR SMOOTH SCROLL
   ============================================================ */
document.querySelectorAll('.nav-right a').forEach(link => {
  link.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (href && href.startsWith('#')) {
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

/* ============================================================
   RELOAD ON BREAKPOINT CROSS
   ============================================================ */
let lastIsMobile = window.innerWidth <= 1000;
window.addEventListener('resize', () => {
  const isMobile = window.innerWidth <= 1000;
  if (isMobile !== lastIsMobile) location.reload();
  lastIsMobile = isMobile;
});

/* ============================================================
   INIT
   ============================================================ */
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('assets/data/recipes.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allRecipes = await res.json();
  } catch (err) {
    console.error('Could not load recipes.json:', err);
    document.getElementById('recipesGrid').innerHTML =
      '<p class="no-results">Failed to load recipes. Make sure assets/data/recipes.json exists.</p>';
    return;
  }

  renderCards(allRecipes);
  setupFilterGroup('seasonFilter', selectedSeasons, allRecipes);
  setupIngredientSearch();
});