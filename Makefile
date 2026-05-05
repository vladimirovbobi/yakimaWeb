# Yakima Real Estate Hub - convenience targets

.PHONY: help assets

help:
	@echo "Targets:"
	@echo "  assets   Generate brand placeholder assets (favicons, hero, samples, OG demos)"

assets:
	python scripts/generate_favicons.py
	python scripts/generate_furniture_remover_samples.py
	python scripts/generate_hero_placeholders.py
	python scripts/generate_post_placeholders.py
	python scripts/generate_service_placeholders.py
	python scripts/generate_avatar_placeholders.py
	python scripts/generate_vendor_logo_placeholders.py
	python scripts/generate_thread_placeholders.py
	docker compose exec api python manage.py regen_og_images --demo
	@echo ""
	@echo "Generated brand asset placeholders. Replace with real assets before launch."
	@echo "See frontend/README.md 'Brand assets' for the full checklist."
