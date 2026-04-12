var MARKER_HEIGHT = 100;
var MARKER_WIDTH = 100;
var MARKER_RADIUS = 50;
var MARKER_EDITABLE = true;
var MARKER_ANGLE = 0;
var DEFAULT_COLOR = '4adc5e';
var DEFAULT_STUDENT_COLOR = 'FBD75B';
var DEFAULT_STUDENT_COLOR_CORRECT = '3994D2';
var DEFAULT_STUDENT_COLOR_WRONG = 'ED1D4F';

var touching_move = false;
document.addEventListener('touchmove', function(e){
    touching_move = true;
}, false);

function Hotspot(canvasID, clickable){
    var self = this;

    canvasID = optionalArg(canvasID, 'canvas');

    self.backgroundImage = null;
    //console.log("Creating Hotspot Canvas, attaching to -> ", canvasID);
    self.clickable = optionalArg(clickable, false);

    self.activeObject = null;

    // A function that can be passed in to the hotspot object
    // will be called on a click of the canvas
    self.onClick = null;
    self.onMouseUp = null;

    // A function that can be passed in to the hotspot object
    // will be called when a new (background) image in placed on the canvas
    self.onPlaceImage = null;


    self.id = canvasID

    self.canvas = new fabric.Canvas(canvasID, {
        selection: false,
        controlsAboveOverlay:true,
        centeredScaling:true,
        allowTouchScrolling: true
    });
    
    self.gesture = false;

    self.canvas.on({
        'touch:gesture': function(e) {
            self.gesture = true;
        },
        'mouse:down': function(e){
            self.gesture = false;
            touching_move = false;
            if (e.target){
                self.activeObject = e.target;
            } else {
                self.activeObject = null;
            }

            if (self.onClick){
                self.onClick();
            }
        },
        'mouse:up': function(e){
            // Place new anwer if no target found and canvas is clickable
            //if (self.clickable && !e.target && self.gesture == false && touching_move == false){
            if (self.clickable && self.gesture == false && touching_move == false){


                self.clearCanvas();
                
                /* is a touch event? */
                if (e.pointer){
                    var mouse_x = e.pointer.x;
                    var mouse_y = e.pointer.y;

                }else if (typeof e.e.touches !== 'undefined') {
                    var mouse_x = e.e.layerX;
                    var mouse_y = e.e.layerY;

                /* it's just the mouse */
                }else{
                    var mouse_x = e.e.offsetX;
                    var mouse_y = e.e.offsetY;
                }

                self.placeStudentAnswer(mouse_x, mouse_y, 0, true);

            }

            if (self.onMouseUp){
                self.onMouseUp();
            }

            if (touching_move == true){
                touching_move = false;
            }
        }
    });

}

Hotspot.prototype.placeImage = function(image){
    var self = this;

    if (self.backgroundImage == null){
        self.backgroundImage = image;
    }
    //console.log("place image -> ", image);
    image = self.backgroundImage;
    //self.clearCanvas();
    fabric.Image.fromURL(image, function(img) {

        var img_size = scaleSize(792, 690, img.width, img.height);

        self.canvas.setHeight(img_size[1]);
        self.canvas.setWidth(img_size[0]);

        img.set({
            width: self.canvas.width,
            height: self.canvas.height,
            originX: 'left',
            originY: 'top'
        });

        self.canvas.setBackgroundImage(img, self.canvas.renderAll.bind(self.canvas), {
          left: 0,
          top: 0,
          originX: 'left',
          originY: 'top',
          crossOrigin: 'anonymous'
        });

    });

    if (self.onPlaceImage){
        self.onPlaceImage();
    }

    if (!image){
        $('#canvas_row').hide();
    }

    self.canvas.renderAll();
};

Hotspot.prototype.clearCanvas = function() {
    var self = this;

    self.canvas.clear().renderAll();
};

Hotspot.prototype.hasImage = function(){
    var self = this;

    var has_img = false;
    if (self.canvas.backgroundImage){
        if(self.canvas.backgroundImage.height && self.canvas.backgroundImage.width){
            has_img = true;
        }
    }
    return has_img;
};

Hotspot.prototype.deleteSelectObject = function(){
    var self = this;

    var obj = self.canvas.getActiveObject();
    self.canvas.remove(obj);
    self.activeObject = null;
};

Hotspot.prototype.getSelectedObject = function(){
    var self = this;

    return self.activeObject;
};

Hotspot.prototype.canPlaceShape = function(){
    var self = this;

    var can_place = true;

    // var objs = self.canvas.getObjects();
    // var obj_count = objs.length;

    if (!self.hasImage()){
        alert("Need to pick an image first");
        can_place = false;
    }

    // if (obj_count > 0) {
    //     alert("Can only place 1 object on the image");
    //     can_place = false;
    // }

    return can_place;
};

Hotspot.prototype.hasShapes = function(){
    var self = this;

    var status = false;

    var obj_count = self.canvas.getObjects().length;
    if (obj_count > 0){
        status = true;
    }

    return status;
};

Hotspot.prototype.changeColor = function(color){
    var self = this;
    console.error("This feature has been removed,");
    // self.canvas.forEachObject(function(obj){
    //     obj.set({
    //         fill: '#'+color,
    //         borderColor: '#'+color,
    //         cornerColor: '#'+color,
    //         stroke: shadeColor('#'+color, -100)
    //     });
    // });

    // self.canvas.renderAll();
};

Hotspot.prototype.placeRectangle = function(x, y, height, width, color, editable){
    var self = this;

    x = optionalArg(x, (self.canvas.getWidth()-MARKER_WIDTH)/2);
    y = optionalArg(y, self.canvas.getHeight()- MARKER_HEIGHT);
    height = optionalArg(height, MARKER_HEIGHT);
    width = optionalArg(width, MARKER_WIDTH);
    editable = optionalArg(editable, MARKER_EDITABLE);
    color = optionalArg(color, DEFAULT_COLOR);

    var rect = new fabric.Rect({
        top: parseInt(y),
        left: parseInt(x),
        width: parseInt(width),
        height: parseInt(height),
        lockRotation: true,
        lockUniScaling: false,
        hasRotatingPoint: false,
        // Commented out because of IE8
        // perPixelTargetFind: true,
        // targetFindTolerance: 4,
        // answerID: '',
        stroke: '#333',
        strokeWidth: 10
    });

    if (!editable){
        rect = no_edit(rect);
    }

    rect = shape_properties(rect, color);

    self.canvas.add(rect);

    return rect;
};


Hotspot.prototype.placeCircle = function(x, y, radius, color, editable){
    var self = this;

    // Add the radius so marker appears fully on screen
    x = optionalArg(x, (self.canvas.getWidth()+MARKER_RADIUS)/2);
    y = optionalArg(y, self.canvas.getHeight() - MARKER_RADIUS);
    radius = optionalArg(radius, MARKER_RADIUS);
    editable = optionalArg(editable, MARKER_EDITABLE);
    color = optionalArg(color, DEFAULT_COLOR);

    var circle = new fabric.Circle({
        top: parseInt(y),
        left: parseInt(x),
        radius: parseInt(radius),
        lockRotation: true,
        lockUniScaling: true,
        hasRotatingPoint: false,
        // Commented out because of IE8
        // perPixelTargetFind: true,
        // targetFindTolerance: 4,
        originX: 'center',
        originY: 'center'
    });

    if (!editable){
        circle = no_edit(circle);
    }
    circle = shape_properties(circle, color);

    self.canvas.add(circle);
    self.canvas.renderAll();
    return circle;
};


Hotspot.prototype.placeTriangle = function(x, y, height, width, angle, color, editable){
    var self = this;

    // Add the width and dived by to to make the triagle fully appear by default
    x = optionalArg(x, (self.canvas.getWidth()-MARKER_WIDTH/2)/2);
    y = optionalArg(y, self.canvas.getHeight()- MARKER_HEIGHT);
    height = optionalArg(height, MARKER_HEIGHT);
    width = optionalArg(width, MARKER_WIDTH);
    angle = optionalArg(angle, MARKER_ANGLE);
    editable = optionalArg(editable, MARKER_EDITABLE);
    color = optionalArg(color, DEFAULT_COLOR);

    var tri = new fabric.Triangle({
        top: parseInt(y),
        left: parseInt(x),
        width: parseInt(width),
        height: parseInt(height),
        // Commented out because of IE8
        // perPixelTargetFind: true,
        // targetFindTolerance: 4,
        angle: parseInt(angle),
        originX: 'center',
        originY: 'top'
    });

    if (!editable){
        tri = no_edit(tri);
    }

    tri = shape_properties(tri, color);

    self.canvas.add(tri);

    return tri;
};

Hotspot.prototype.getShape = function(){
    var self = this;
    return self.canvas.getObjects()[0];
};

Hotspot.prototype.getJSON = function(){
    // Gets all the objects on the canvas,
    // There should only be one oject on the canvas for get that object
    var obj = this.getShape();

    var obj_list = [];

    this.canvas.forEachObject(function(obj){
        var points = get_points_string(obj, obj.type, obj.oCoords);

        var radius = 'None';
        if (obj.hasOwnProperty("radius")) {
            radius = Math.round(obj.radius * obj.scaleX);
            if (isNaN(radius)){
                radius = 'None';
            }
        }

        var hs_id = 'None';
        if ( obj.hotspotID ){
            hs_id = obj.hotspotID;
        }

        var json_obj = {
            'hs_id': hs_id,
            'type': obj.type,
            'height': Math.round(obj.height * obj.scaleY),
            'width': Math.round(obj.width * obj.scaleX),
            'radius': radius,
            'points': points,
            'angle': Math.round(obj.angle)
        };

        obj_list.push(json_obj);
    });

    // This returns the JSON object as a string
    // Server will convert it to usable code
    var json_string = JSON.stringify(obj_list);

    return json_string;
};


Hotspot.prototype.placeCorrectAnswer = function(shape, editable){
    var self = this;
    var status = false;

    var shapeObj = null;

    // REASON: override any student colors with the default student color
    // if(!shape.color){
        shape.color = DEFAULT_STUDENT_COLOR;
    // }

    //console.log("Placing shape on -> ", self.id)

    if (shape.shape.toUpperCase() === 'R') {
        shapeObj = self.placeRectangle(shape.x1, shape.y1, shape.height, shape.width, shape.color, editable);
        status = true;
    } else if (shape.shape.toUpperCase() === 'C') {
        shapeObj = self.placeCircle(shape.x1, shape.y1, shape.radius, shape.color, editable);
        status = true;
    } else if (shape.shape.toUpperCase() === 'T') {
        shapeObj = self.placeTriangle(shape.x1, shape.y1, shape.height, shape.width, shape.angle, shape.color, editable);
        status = true;
    }

    return status;

};

Hotspot.prototype.getAndPlaceCorrectAnswer = function(editable, questionNumber){
    var self = this;
    var status = false;

    questionNumber = optionalArg(questionNumber, '');

    if (questionNumber){
        questionNumber = '_' + questionNumber;
    }

    var height = $('#shape_height' + questionNumber).val();
    var radius = $('#shape_radius'+ questionNumber).val();
    var shape = $('#shape_shape' + questionNumber).val().toUpperCase();
    var width = $('#shape_width' + questionNumber).val();
    var angle = $('#shape_angle' + questionNumber).val();
    var x1 = $('#shape_x1' + questionNumber).val();
    var y1 = $('#shape_y1' + questionNumber).val();
    var x2 = $('#shape_x2' + questionNumber).val();
    var y2 = $('#shape_y2' + questionNumber).val();
    var x3 = $('#shape_x3' + questionNumber).val();
    var y3 = $('#shape_y3' + questionNumber).val();

    var color = DEFAULT_COLOR;

    if (shape === 'R') {
        var rect = self.placeRectangle(x1, y1, height, width, color, editable);
        rect.isAnswer = true;
        status = true;
    } else if (shape === 'C') {
        var circle = self.placeCircle(x1, y1, radius, color, editable);
        circle.isAnswer = true;
        status = true;
    } else if (shape === 'T') {
        var triangle = self.placeTriangle(x1, y1, height, width, angle, color, editable);
        triangle.isAnswer = true;
        status = true;
    }
    return status;
};

Hotspot.prototype.renderAll = function(){
    var self = this;
    self.canvas.renderAll();
};

Hotspot.prototype.findObjByUserIDandCoords = function(userID, x, y){
    var self = this;

    var return_value = false;

    self.canvas.forEachObject(function(obj){
         if(userID == obj.userid && obj.top == y && obj.left == x){
             return_value = obj;
         }
    });

    return return_value;
};

Hotspot.prototype.isInsideAnswer = function(x, y){
    var self = this;

    //console.log("is Inside");

    var answer = null;
    var return_value = false;


    self.canvas.forEachObject(function(obj){
        if (obj.isAnswer){
            answer = obj;
        }
    });

    if (answer){
        var point = new fabric.Point(x, y);
        return_value = answer.containsPoint(point);
    }

    return return_value;
};

Hotspot.prototype.placeStudentAnswer = function(x, y, userid, dragable){
    var self = this;

    userid = optionalArg(userid, null);

    dragable = optionalArg(dragable, false);

    var circle = new fabric.Circle({
        top: parseInt(y),
        left: parseInt(x),
        radius: 10,
        lockRotation: true,
        lockUniScaling: true,
        hasRotatingPoint: false,
        // perPixelTargetFind: true,
        targetFindTolerance: 4,
        originX: 'center',
        originY: 'center',
        fill : '#' + DEFAULT_STUDENT_COLOR,
        opacity : 0.8,
        borderColor : shadeColor('#' + DEFAULT_STUDENT_COLOR, 1),
        cornerColor : shadeColor('#' + DEFAULT_STUDENT_COLOR, 1),
        cornerSize : 10,
        transparentCorners : false,
        strokeWidth: 4,
        stroke: shadeColor('#' + DEFAULT_STUDENT_COLOR, 1),
    });

    if (!dragable){
        circle = no_edit(circle);
    } else {
        circle.selectable = true;
        circle.hasBorders = false;
        circle.hasControls = false;
    }

    circle.userid = userid;
    self.canvas.add(circle);
    self.placeImage(null);
    self.updateQuestionFormAnswer();
};

Hotspot.prototype.placeStudentAnswerReview = function(x, y, userid, dragable, iscorrect=true){
    var self = this;
    userid = optionalArg(userid, null);
    dragable = optionalArg(dragable, false);
    iscorrect = optionalArg(iscorrect, true);

    if (iscorrect== true){
        fill_color = DEFAULT_STUDENT_COLOR_CORRECT;
    }else{
        fill_color = DEFAULT_STUDENT_COLOR_WRONG;
    }

    var circle = new fabric.Circle({
        top: parseInt(y),
        left: parseInt(x),
        radius: 10,
        lockRotation: true,
        lockUniScaling: true,
        hasRotatingPoint: false,
        // perPixelTargetFind: true,
        targetFindTolerance: 4,
        originX: 'center',
        originY: 'center',
        fill : '#' + fill_color,
        opacity : 0.8,
        borderColor : shadeColor('#' + fill_color, 1),
        cornerColor : shadeColor('#' + fill_color, 1),
        cornerSize : 10,
        transparentCorners : false,
        strokeWidth: 4,
        stroke: shadeColor('#' + fill_color, 1),
    });

    if (!dragable){
        circle = no_edit(circle);
    } else {
        circle.selectable = true;
        circle.hasBorders = false;
        circle.hasControls = false;
    }

    circle.userid = userid;
    self.canvas.add(circle);
    self.placeImage(null);
    self.updateQuestionFormAnswer();
};

Hotspot.prototype.updateQuestionFormAnswer = function(){
    var self = this;
    var marker = self.getShape();
    console.log(marker);
    if (marker) {
        var center = marker.getCenterPoint();
        if ($('#response')){
            $('#response').val( center.x + '|' + center.y );
        }
    }
}

// Scales the size of an image
function scaleSize (maxW, maxH, currW, currH){
    var ratio = currH / currW;

    if (currW >= maxW && ratio <= 1) {
        currW = maxW;
        currH = currW * ratio;
    } else if (currH >= maxH) {
        currH = maxH;
        currW = currH / ratio;
    }

    return [currW, currH];
}

// Gets the color for the shape
function get_shape_color(){
    console.error("Feature has been removed.");
    // var color = $('#color-list [type="radio"]:checked').val();
    // if (color){
    //     return color;
    // } else {
    //     return DEFAULT_COLOR;
    // }
    return DEFAULT_COLOR;
}

// Gets the points for the obj, in a string format
function get_points_string(obj, obj_type, coords) {
    var points = false;

    if (obj_type == 'rect') {
        // Gets the top-left point of the rectangle
        var top_left_x = coords.tl.x;
        var top_left_y = coords.tl.y;

        var top_left_point = point_to_string(top_left_x, top_left_y);
        points = top_left_point;

    } else if (obj_type == 'triangle') {
        // Gets all 3 points of the triangle

        // Reason all 3 points are needed is for server side checking

        // Gets top point of triangle
        var top_x = coords.mt.x;
        var top_y = coords.mt.y;
        var top_point = point_to_string(top_x, top_y);

        // Gets bottom left of triangle
        var bottom_left_x = coords.bl.x;
        var bottom_left_y = coords.bl.y;
        var bottom_left_point = point_to_string(bottom_left_x, bottom_left_y);

        // Gets bottom right of triangle
        var bottom_right_x = coords.br.x;
        var bottom_right_y = coords.br.y;
        var bottom_right_point = point_to_string(bottom_right_x, bottom_right_y);

        points = top_point + ',' + bottom_left_point + ',' + bottom_right_point;

    } else if (obj_type == 'circle') {

        // For a circle we need the center, not the top left point
        var center = obj.getCenterPoint();

        var center_point = point_to_string(center.x, center.y);

        points = center_point;
    }

    return '[' + points + ']';
}

// Used to convert the point into a string for the server
function point_to_string(x, y) {
    var p_string = '(' + Math.round(x) + ', ' + Math.round(y) + ')';
    return p_string;
}

// Used for optional parameters into a function
function optionalArg(arg, default_value){
    if ( typeof arg === 'undefined' ) {
        arg = default_value;
    }
    return arg;
}

// Shape properties for locking a shape
function no_edit(obj){

    obj.lockMovementX = true;
    obj.lockMovementY = true;
    obj.selectable = false;
    obj.hasBorders = false;
    obj.hasControls = false;
    obj.hoverCursor = 'normal';

    return obj;
}

function shadeColor(color, shade) {
        var colorInt = parseInt(color.substring(1),16);

        var R = (colorInt & 0xFF0000) >> 16;
        var G = (colorInt & 0x00FF00) >> 8;
        var B = (colorInt & 0x0000FF) >> 0;

        R = R + Math.floor((shade/255)*R);
        G = G + Math.floor((shade/255)*G);
        B = B + Math.floor((shade/255)*B);

        var newColorInt = (R<<16) + (G<<8) + (B);
        var newColorStr = "#"+newColorInt.toString(16);

        return newColorStr;
}

// Standard Shape properties
function shape_properties(obj, color){

    var color = '#4adc5e';
    var borderColor = '#00A651';

    obj.fill = color;
    obj.opacity = 0.5;
    obj.borderColor = borderColor;

    obj.cornerColor = color;
    obj.cornerSize = 10;
    obj.transparentCorners = false;

    // This is the border that is around the shape object
    obj.stroke = borderColor;
    // REASON: commented out because it is now a static colored shape
    // obj.stroke = shadeColor('#'+color, -100);
    obj.strokeWidth = 5;

    // This is used for when the object is scaling
    // So the stoke (border) of the shape object stay the same
    obj.on({
        'scaling': function(e) {
            var obj = this,
                w = obj.width * obj.scaleX,
                h = obj.height * obj.scaleY,
                r = obj.radius * obj.scaleX,
                s = obj.strokeWidth;

            obj.set({
                'height'     : h,
                'width'      : w,
                'radius'     : r,
                'scaleX'     : 1,
                'scaleY'     : 1
            });
        }
    });


    return obj;
}