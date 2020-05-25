import json

from smallab.file_locations import get_experiment_save_directory, get_save_directory
from smallab.runner_implementations.multiprocessing_runner import MultiprocessingRunner

if __name__ == "__main__":

    import typing
    import random
    import os
    import dill

    # What you need to import from smallab
    from smallab.experiment_types.experiment import Experiment
    from smallab.runner import ExperimentRunner


    # Write a simple experiment
    class SimpleExperiment(Experiment):
        # Need to implement this method, will be passed the specification
        # Return a dictionary of results
        def main(self, specification: typing.Dict) -> typing.Dict:
            self.get_logger_name().info("Doing work!")
            random.seed(specification["seed"])
            for i in range(specification["num_calls"]):  # Advance the random number generator some amount
                random.random()
            if "fail" in specification and specification["fail"]:
                raise Exception()
            return {"number": random.random()}


    runner = ExperimentRunner()

    # Optional: Email yourself when the whole batch is done
    # Read https://stackoverflow.com/questions/5619914/sendmail-errno61-connection-refused about how to start an stmp serevr
    from smallab.utilities.email_hooks import EmailCallbackBatchOnly

    runner.attach_callbacks([EmailCallbackBatchOnly("test@test.com", 40)])
    # Take it back off since we don't actually want to bother Mr. Test
    runner.attach_callbacks([])

    # Set the specifications for our experiments, the author reccomends reading this from a json file!
    specifications = [{"seed": 1, "num_calls": 1}, {"seed": 2, "num_calls": 1}]

    # Fire off the experiment
    runner.run("random_number", specifications, SimpleExperiment())

    # Read back our results. Smallab will attempt to save the file in json format so you can easily read
    # it but will fall back to pickle if necessary.
    for root, _, files in os.walk(get_experiment_save_directory("random_number")):
        for fname in files:
            if ".json" in fname:
                with open(os.path.join(root, fname), "r") as f:
                    results = json.load(f)
                    print(results["specification"]["seed"])
                    print(results["result"]["number"])

    from smallab.specification_generator import SpecificationGenerator

    # If you want to run a lot of experiments but not manual write out each one, use the specification generator.
    # Note: This is also JSON serializable, so you could store this in a json file
    generation_specification = {"seed": [1, 2, 3, 4, 5, 6, 7, 8], "num_calls": [1, 2, 3]}

    # Call the generate method. Will create the cross product.
    specifications = SpecificationGenerator().generate(generation_specification)
    print(specifications)

    runner.run("random_number_from_generator", specifications, SimpleExperiment(), continue_from_last_run=True)

    # Read back our results
    for root, _, files in os.walk(get_save_directory("random_number_from_generator")):
        for fname in files:
            if ".pkl" in fname:
                with open(os.path.join(root, fname), "rb") as f:
                    results = dill.load(f)
                    print(results["specification"]["seed"])
                    print(results["result"]["number"])

    # If you have an experiment you want run on a lot of computers you can use the MultiComputerGenerator
    # You assign each computer a number from 0..number_of_computers-1 and it gives each computer every number_of_computerth specification
    from smallab.specification_generator import MultiComputerGenerator

    all_specifications = SpecificationGenerator().from_json_file('test.json')

    g1 = MultiComputerGenerator(0, 2)
    g2 = MultiComputerGenerator(1, 2)
    specifications_1 = g1.from_json_file("test.json")
    specifications_2 = g2.from_json_file("test.json")

    assert len(specifications_1) + len(specifications_2) == len(all_specifications)

    # Need to freeze the sets in order to do set manipulation on dictionaries
    specifications_1 = set([frozenset(sorted(x.items())) for x in specifications_1])
    specifications_2 = set([frozenset(sorted(x.items())) for x in specifications_2])
    all_specifications = set([frozenset(sorted(x.items())) for x in all_specifications])

    # This will generate two disjoint sets of specifications
    assert specifications_1.isdisjoint(specifications_2)
    # That together make the whole specification
    assert specifications_1.union(specifications_2) == all_specifications

    # You can use the provided logging callbacks to log completion and failure of specific specifcations

    runner.run('with_logging', SpecificationGenerator().from_json_file("test.json"), SimpleExperiment(),
               continue_from_last_run=True, specification_runner=MultiprocessingRunner())
