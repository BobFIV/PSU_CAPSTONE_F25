cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(seeed)

target_sources(app PRIVATE 
    src/main.c
    src/sense_collect.c
    src/mlx90614.c
    )

    target_include_directories(app PRIVATE inc)
