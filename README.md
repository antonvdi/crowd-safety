# crowd-safety

## documents

[documents](./documents/) includes deliverable artifacts written with [Quarto](https://quarto.org/). It should include the latest .pdf version of the .qmd file as well. If not, then the Quarto document can be rendered by following [this guide](https://quarto.org/docs/tools/vscode.html).

## diagrams

[diagrams](./diagrams/) includes deliverable UML (or UML-like) diagrams written usen the [Plant UML mark up langauge](https://plantuml.com/). The diagrams can be rendered [here](http://www.plantuml.com/plantuml/uml/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000).


## ucloud
Clone the git repository in a UCloud instance with access to CUDA. Run the "backend/init.sh" script to prepare the environment. Then run main.py with the wanted parameters.

```bash
git clone https://github.com/anirv20/crowd-safety.git
bash backend/init.sh
```

**local_coords** are the coordinates on the video frames (starting in upper left corner and going clockwise) in pixel value pairs (x,y) when resized to 1920x1080. 
**global_coords** are the coordinates of the expected output video. One pixel here is equal to one unit (i.e. meters) in the real world domain.