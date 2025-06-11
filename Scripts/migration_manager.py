class MigrationManager:
    def __init__(self, processor, years):
        self.processor = processor
        self.years = years

    def run(self):
        last_year = "0000"
        for year in self.years:
            self.processor.pull_slice(year, last_year)
            last_year = year
