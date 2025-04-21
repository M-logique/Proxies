import "./style.css";

async function fetchJSON(url) {
	try {
		const response = await fetch(url);
		if (!response.ok) return null;
		return await response.json();
	} catch (e) {
		return null;
	}
}

class Toaster {
	constructor(maxActive = 4, duration = 3000, animationDuration = 300) {
	  this.container = document.getElementById('toast-container');
	  this.template = document.getElementById('toast-template');
	  this.maxActive = maxActive;
	  this.duration = duration;
	  this.animDur = animationDuration;
	  this.queue = [];
	  this.active = [];
	}

	show(message) {
	  const toast = this._createToast(message);
	  if (this.active.length < this.maxActive) {
		this._display(toast);
	  } else {
		this.queue.push(toast);
	  }
	}

	_createToast(message) {
	  const toast = this.template.cloneNode(true);
	  toast.removeAttribute('id');
	  toast.classList.remove("hidden");
	  const contentEl = toast.querySelector('.toast-content');
	  contentEl.textContent = message;
	  return toast;
	}

	_display(toast) {
	  this.container.appendChild(toast);
	  this.active.push(toast);

	  // Animate in
	  toast.animate(
		[
		  { transform: 'translateY(20px)', opacity: 0 },
		  { transform: 'translateY(0)', opacity: 1 }
		],
		{ duration: this.animDur, easing: 'ease-out', fill: 'forwards' }
	  );

	  // Schedule dismiss
	  setTimeout(() => this._dismiss(toast), this.duration);
	}

	_dismiss(toast) {
	  // Animate out
	  const anim = toast.animate(
		[
		  { transform: 'translateY(0)', opacity: 1 },
		  { transform: 'translateY(20px)', opacity: 0 }
		],
		{ duration: this.animDur, easing: 'ease-in', fill: 'forwards' }
	  );
	  anim.onfinish = () => {
		this.container.removeChild(toast);
		this.active = this.active.filter(t => t !== toast);
		if (this.queue.length) {
		  const next = this.queue.shift();
		  this._display(next);
		}
	  };
	}
  }

window.addEventListener("load", async () => {

	const data = await fetchJSON("https://raw.githubusercontent.com/M-logique/Proxies/refs/heads/main/proxies/byLocation.json");
	const convert = await fetchJSON("https://raw.githubusercontent.com/M-logique/Proxies/refs/heads/main/server/countries.json");
	
	function getCodeFromCountryName(name) {
		const match = convert.find(c => c.name.toLowerCase() === name.toLowerCase());
		return match ? match.code : null;
	}
	function countryCodeToFlag(countryCode) {
		return countryCode
			.toUpperCase()
			.split('')
			.map(char => String.fromCharCode(0x1F1E6 - 65 + char.charCodeAt(0)))
			.join('');
	}
	
	const select = document.querySelector("#country-select");
	const configs = document.querySelector("#configs");
	const sub = document.querySelector("#subscription");

	let total = data.locations.totalCountries;
	for (let i = 0; i < total; i++) {
		const option = document.createElement("option");
		const name = data.locations.byNames[i];
		const cc = getCodeFromCountryName(name)
		option.value = cc;
		option.text = `${countryCodeToFlag(cc)} ${name}`;
		select.appendChild(option);
	}

	const toaster = new Toaster();


	select.addEventListener('change', function() {
		configs.innerHTML = '';
		const value = select.options[select.selectedIndex].value;

		sub.querySelector(".config-url").textContent = "https://1oi.xyz/proxies/v2ray/location/" + value;

		let i = 1;
		data.profilesByCountryCode[value].forEach(item => {
			const template = document.querySelector('#config-template');
			const clone = template.cloneNode(true);
			clone.removeAttribute('id');
			clone.classList.remove('hidden');
			clone.querySelector('.config-url').textContent = item;
			clone.querySelector('.config-num').textContent = i;
			configs.appendChild(clone);
			i++;
		});
		document.querySelectorAll('.copy-config').forEach(button => {
			button.addEventListener('click', () => {
				const url = button.parentElement.querySelector('.config-url').textContent;
				navigator.clipboard.writeText(url);
				toaster.show("Successfully copied to clipboard.");
			});
		});
	});

});