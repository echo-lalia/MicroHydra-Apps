import yaml
import os



CWD = os.getcwd()
APP_SOURCE = os.path.join(CWD, 'app-source')



# load default app description
with open(os.path.join(APP_SOURCE, 'default.yml'), 'r', encoding="utf-8") as default_file:
    DEFAULT_DETAILS = yaml.safe_load(default_file.read())






def main():
    # load each directory in APP_SOURCE as an AppSource object
    app_sources = [AppSource(dir_entry) for dir_entry in os.scandir(APP_SOURCE) if dir_entry.is_dir()]
    
    for app in app_sources:
        app.make_readme()









class AppSource:

    def __init__(self, dir_entry):
        self.dir_entry = dir_entry
        self.name = dir_entry.name

        self.details = DEFAULT_DETAILS.copy()

        # load app details if they exist:
        try:
            details_path = os.path.join(APP_SOURCE, self.name, 'details.yml')
            with open(details_path, 'r', encoding="utf-8") as detail_file:
                self.details.update(
                    yaml.safe_load(detail_file.read())
                )
        except FileNotFoundError:
            print(f"WARNING: App {self.name} has no details.yml")
            

    def __repr__(self):
        return f"AppSource({self.name})"


    def make_readme(self):
        """
        Generate README.md file for this app
        """

        # make linked author string
        if self.details['author_link']:
            author_string = f"[{self.details['author']}]({self.details['author_link']})"
        else:
            author_string = self.details['author']
        
        # do the same for license string
        license_string = f"[{self.details['license']}]({self.details['license_link']})"

        # assemble this app's README.md file
        readme = f"""\
<!---
This file is generated from the "details.yml" file. (Any changes here will be overwritten)
--->
# {self.name}
> Author: **{author_string}** | License: **{license_string}** | Version: **{self.details['app_version']}**  
<br/>

{self.details['description']}

<br/><br/>

-----
### Installation:
{self.details['installation_instructions']}

"""     
        # finally, write that file
        with open(os.path.join(APP_SOURCE, self.name, 'README.md'), 'w', encoding="utf-8") as readme_file:
            readme_file.write(readme)

main()
