import json
import os
from time import sleep

class StatisticsSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.full_statistics = False
            cls._instance.pymop_start_time = 0.0
            cls._instance.instrumentation_end_time = 0.0
            cls._instance.instrumentation_duration = 0.0
            cls._instance.create_monitor_end_time = 0.0
            cls._instance.create_monitor_duration = 0.0
            cls._instance.full_statistics_dict = {}  # to monitor and events
            cls._instance.violations_dict = {}  # only to violations
            cls._instance.file_name = None
            cls._instance.current_test = None
        return cls._instance

    def print_statistics(self):
        """
        Print or save both monitor and violation statistics.
        """

        print("Generating statistics...")
        sleep(0.1)
        self._print_statistics_time()
        self._print_statistics_monitor_and_events()
        self._print_statistics_violations()

    def _print_statistics_time(self):
        """
        Print the tool time measurements
        """
        print_msg = f"=========================== Time Measurements ===========================\n"

        # Print out the elapsed time for importing specs and instrumentation.
        print_msg += f"PyMOP start time: {self.pymop_start_time:.5f} seconds\n"
        print_msg += f"Instrumentation end time: {self.instrumentation_end_time:.5f} seconds\n"
        print_msg += f"Time taken for instrumentation: {self.instrumentation_duration:.5f} seconds\n"
        print_msg += f"Create monitor end time: {self.create_monitor_end_time:.5f} seconds\n"
        print_msg += f"Time taken for creating monitors: {self.create_monitor_duration:.5f} seconds\n"

        if self.file_name:
            basename, ext = os.path.splitext(self.file_name)
            new_file_name = basename + '-time' + ext
            dict_message = {'pymop_start_time': self.pymop_start_time,
                            'instrumentation_end_time': self.instrumentation_end_time,
                            'instrumentation_duration': self.instrumentation_duration,
                            'create_monitor_end_time': self.create_monitor_end_time,
                            'create_monitor_duration': self.create_monitor_duration}
            self._save_in_file(new_file_name, print_msg, dict_message)
            print(f"Time measurements are saved in {new_file_name}.")
        else:
            print(print_msg)

    def _print_statistics_violations(self):
        """
        Print or save violation statistics.
        """
        print_msg = f"============================== Violations ==============================\n"
        total = 0
        for spec_name, violations in self.violations_dict.items():
            spec_total = sum(info.get('count', 0) for info in violations.values())
            total += spec_total
            print_msg += f"Spec - {spec_name}: {spec_total} violations\n"

        print_msg += f"Total Violations: {total} violations\n"
        print_msg += f"------------\n"
        for spec_name, violations in self.violations_dict.items():
            print_msg += f"Spec - {spec_name}:\n"
            for violation, info in violations.items():
                num = info.get('count', 0)
                tests = info.get('test', set())
                print_msg += f"    {violation}, (Tests: {tests}): {num} times\n"
            print_msg += f"------------\n"

        if self.file_name:
            basename, ext = os.path.splitext(self.file_name)
            new_file_name = basename + '-violations' + ext
            self._save_in_file(new_file_name, print_msg, self.violations_dict)
            print(f"Violations are saved in {new_file_name}.")
        else:
            print(print_msg)

    def _print_statistics_monitor_and_events(self):
        """
        Print or save monitor and events statistics.
        """
        if self.full_statistics:
            print_msg = (f"============================== Monitors and Events calls "
                         f"==============================\n")
            total = 0
            for spec_name in self.full_statistics_dict.keys():
                num = self.full_statistics_dict[spec_name]['monitors']
                total += num
                print_msg += f"Spec - {spec_name}: {num} monitors\n"
            print_msg += f"Total Monitors: {total} monitors\n"
            print_msg += f"------------\n"
            for spec_name in self.full_statistics_dict.keys():
                print_msg += f"Spec - {spec_name}:\n"
                for event in self.full_statistics_dict[spec_name]['events']:
                    num = self.full_statistics_dict[spec_name]['events'][event]
                    print_msg += f"    {event}: {num} times\n"
                print_msg += f"------------\n"

            if self.file_name:
                basename, ext = os.path.splitext(self.file_name)
                new_file_name = basename + '-full' + ext
                self._save_in_file(new_file_name, print_msg, self.full_statistics_dict)
                print(f"Full statistics are saved in {new_file_name}.")
            else:
                print(print_msg)
    def _save_in_file(self, new_file_name, print_msg, message_dict):
        with open(new_file_name, 'w') as f:
            if self.file_name.endswith('.json'):
                serializable = self._make_json_serializable(message_dict)
                json.dump(serializable, f, indent=2)
            else:
                f.write(print_msg)

    def _make_json_serializable(self, obj):
        """
        Recursively convert objects not serializable by json (e.g., set, tuple)
        into JSON-friendly structures. Sets/tuples -> lists; dict keys preserved.
        """
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        if isinstance(obj, set):
            # Convert to a stable order for determinism
            try:
                return sorted(self._make_json_serializable(item) for item in obj)
            except TypeError:
                # Fallback when elements are not directly comparable
                return [self._make_json_serializable(item) for item in obj]
        return obj

    def add_pymop_start_time(self, pymop_start_time):
        """
        Update instrumentation duration statistics.
        """
        self.pymop_start_time = pymop_start_time

    def add_instrumentation_duration(self, instrumentation_end_time, instrumentation_duration):
        """
        Update instrumentation duration statistics.
        """
        self.instrumentation_end_time = instrumentation_end_time
        self.instrumentation_duration = instrumentation_duration

    def add_create_monitor_duration(self, create_monitor_end_time, create_monitor_duration):
        """
        Update import duration statistics.
        """
        self.create_monitor_end_time = create_monitor_end_time
        self.create_monitor_duration = create_monitor_duration

    def add_monitor_creation(self, spec_name):
        """
        Add monitor creation to statistics count.
        """
        if self.full_statistics:
            if spec_name not in self.full_statistics_dict:
                self.full_statistics_dict[spec_name] = {'monitors': 0, 'events': {}}
            self.full_statistics_dict[spec_name]['monitors'] += 1

    def add_violation(self, spec_name, violation):
        """
        Add violation to statistics with associated current test information.
        """
        violation_first_occurrence = True
        if spec_name not in self.violations_dict:
            self.violations_dict[spec_name] = {}

        violation_path = 'file_name: ' + violation.split('file_name: ')[1]
        target_violation = None
        for existing_violation in self.violations_dict[spec_name]:
            if violation_path in existing_violation:
                violation_first_occurrence = False
                target_violation = existing_violation
        
        if violation_first_occurrence:
            self.violations_dict[spec_name][violation] = {}
            self.violations_dict[spec_name][violation]['count'] = 0
            self.violations_dict[spec_name][violation]['test'] = set()
        else:
            violation = target_violation

        self.violations_dict[spec_name][violation]['count'] += 1
        self.violations_dict[spec_name][violation]['test'].add(self.current_test)
        return violation_first_occurrence

    def update_violation_message(self, spec_name, old_violation, new_violation):
        """
        Update the violation message to use the custom message defined by the user.
        """
        if spec_name not in self.violations_dict:
            return
        if old_violation not in self.violations_dict[spec_name]:
            return
        temp_violation = self.violations_dict[spec_name][old_violation]
        self.violations_dict[spec_name][new_violation] = temp_violation
        self.violations_dict[spec_name].pop(old_violation)

    def add_events(self, spec_name, event_name):
        """
        Add event to statistics.
        """
        if self.full_statistics:
            if spec_name not in self.full_statistics_dict:
                self.full_statistics_dict[spec_name] = {'monitors': 0, 'events': {}}
            if event_name not in self.full_statistics_dict[spec_name]['events']:
                self.full_statistics_dict[spec_name]['events'][event_name] = 0
            self.full_statistics_dict[spec_name]['events'][event_name] += 1

    def set_current_test(self, test_name):
        """
        Add current test name and location to statistics.
        """
        self.current_test = test_name

    def set_full_statistics(self):
        """
        Set the statistics to be full.
        It will print out all the
        violations and the monitors count.
        """
        self.full_statistics = True

    def set_file_name(self, file_name):
        """
        Set the file name for saving the statistics.
        """
        self.file_name = file_name