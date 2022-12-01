This folder has been created to store all the output files after the execution of the simulation.

Each simulation will have its own output directory inside this folder. The output directory name is determined by:

`output/<coupled_model_name>-<time_stamp>`, where:

- `coupled_model_name` will be the name of the root coupled model. 
- `<time_stamp>` will be a timestamp mark (yyyymmddhhmmss), correspoding to the instant in which the simulation was executed.

Obviously, the content of this folder must not be followed by the git repository.
