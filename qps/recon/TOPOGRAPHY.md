# CoolProp foreign-land topography

Evidence baseline: `GBOGEB/CoolProp@a3c743026521ff557f8c2e85701c726898b00e0b`.

```text
CoolProp/
├── README.md                  narrative / project orientation
├── LICENSE                    MIT licence
├── CMakeLists.txt             root C++ build and feature switches
├── pyproject.toml             Python packaging via scikit-build-core
├── .gitmodules                external source/build dependencies
├── .github/workflows/         CI, wrapper, docs, shared-library surfaces
├── include/
│   ├── CoolProp.h             high-level C++ public API
│   ├── AbstractState.h        state abstraction contract
│   └── ...
├── src/
│   ├── CoolProp.cpp           PropsSI/PropsSImulti high-level implementation
│   ├── AbstractState.cpp      backend factory + common state interface
│   └── Backends/
│       ├── Helmholtz/         HEOS/Helmholtz implementation and flash routines
│       ├── Cubics/
│       ├── IF97/
│       ├── Incompressible/
│       ├── PCSAFT/
│       ├── REFPROP/
│       └── Tabular/
├── dev/
│   └── fluids/
│       └── Helium.json        helium EOS, states and ancillary data
├── externals/                 submodules / vendored build dependencies
├── wrappers/                  broad language/application integration layer
│   ├── Python/
│   ├── Excel/
│   ├── MATLAB/
│   ├── Fortran/
│   ├── Javascript/
│   ├── Julia/
│   ├── Labview/
│   ├── EES/
│   └── ...
└── qps/recon/                 local reconnaissance overlay only
```

## Primary penetration path

```text
QPS caller
  -> PropsSI(..., "HEOS::Helium")
  -> src/CoolProp.cpp::_PropsSImulti
  -> _PropsSI_initialize
  -> AbstractState::factory
  -> HEOS backend generator
  -> Helmholtz EOS state / flash routines
  -> Helium model data
  -> state update
  -> keyed property output
  -> QPS receipt
```

## Border observations

- The root project is not a single algorithm; public API, abstract state selection, backend implementations, fluid data, wrappers and CI are separate surfaces.
- The Python build recursively compiles `src/*.cpp` into the extension and generates headers from fluid JSON inputs.
- `.gitmodules` binds Catch2, Eigen, IF97, REFPROP headers, fmt, msgpack, rapidjson, pybind11, multicomplex and other external components.
- Wrappers demonstrate that the stable reusable opportunity is the property contract and provenance layer, not copying a particular wrapper wholesale.
- The QPS overlay must remain separable from upstream-owned physics implementation.

## Reader state

- Reader-1 / Cartographer: `PASS` for first-pass orientation.
- Reader-2 / EntryPoint: `PASS` for public `PropsSI` path.
- Reader-3 / DeepReader: `PARTIAL` until runtime receipt confirms the full helium path executes on this branch.
