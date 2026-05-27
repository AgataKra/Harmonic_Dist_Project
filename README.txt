Simulation-Based Demonstrator for Harmonic Distortion in Power Supply Networks

Run the GUI:

    python main.py

On this Linux development setup the virtual environment can be used directly:

    .venv/bin/python main.py

The program simulates a six-pulse rectifier through PySpice and
ngspice. Netlist for this rectifier is stored in the project.

The GUI also supports sweep simulations. Use "Run sweep" to select one editable
component parameter, enter 3 to 5 values, and compare all resulting simulations
on shared interactive plots.

Main files:

    main.py                         GUI entry point
    window_manage.py                Compatibility launcher for the GUI
    gui/app.py                      Main Tkinter form and simulation orchestration
    gui/sweep.py                    Sweep dialog and sweep case model
    gui/results.py                  Result windows, graph tabs, and harmonic tables
    gui/plotting.py                 Shared matplotlib toolbar and reset-view helper
    spice_simulation.py             PySpice runner and harmonic analysis
    netlists/six_pulse_rectifier.net Base circuit netlist
    img/rectifier_diag_placeholder.png Circuit image displayed by the GUI
