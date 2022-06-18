build:
	python -m build

test:
	coverage run -m unittest tests
	coverage html
	coverage report

typecheck:
	mypy -m config_init
