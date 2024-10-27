import os


class LocaleTracking:
    def __init__(self, local_folder: str):
        self.local_folder = local_folder

    def get_files_in_local_folder(self) -> set[str]:
        return set(os.listdir(self.local_folder))

    def get_files_and_latest_modification(
        self, locale_files: set[str]
    ) -> dict[str, float]:
        return {
            filename: os.path.getmtime(os.path.join(self.local_folder, filename))
            for filename in locale_files
        }
