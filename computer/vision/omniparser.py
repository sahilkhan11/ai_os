import sys
import os
import time

class OmniParserBridge:
    def __init__(self, weights_dir="/opt/OmniParser/weights"):
        self.weights_dir = weights_dir
        self.device = "cpu"
        self._initialized = False
        self.som_model = None
        self.caption_model_processor = None
        
        if "/opt/OmniParser" not in sys.path:
            sys.path.append("/opt/OmniParser")

    def _initialize(self):
        if self._initialized:
            return
            
        print("Loading OmniParser models on CPU (this takes a moment)...")
        try:
            from util.utils import get_som_labeled_img, get_caption_model_processor, get_yolo_model
            self.get_som_labeled_img = get_som_labeled_img
        except ImportError as e:
            raise ImportError(f"Could not import OmniParser modules from /opt/OmniParser: {e}. Is it installed?")
            
        yolo_model_path = os.path.join(self.weights_dir, "icon_detect", "model.pt")
        caption_model_path = os.path.join(self.weights_dir, "icon_caption")
        
        self.som_model = get_yolo_model(model_path=yolo_model_path)
        self.caption_model_processor = get_caption_model_processor(
            model_name="florence2", 
            model_name_or_path=caption_model_path,
            device=self.device
        )
        self._initialized = True
        print("OmniParser loaded.")

    def parse(self, image_path: str):
        self._initialize()
        
        print("Parsing screenshot with OmniParser (CPU)...")
        start_time = time.time()
        
        # Typically returns (labeled_img, label_coordinates, parsed_content_list)
        # We only need the parsed structured content
        try:
            result = self.get_som_labeled_img(
                image_path,
                self.som_model,
                BOX_TRESHOLD=0.05,
                output_coord_in_ratio=True,
                ocr_bbox=[],
                draw_bbox_config={"text_scale": 0.8, "text_thickness": 2, "text_padding": 3, "thickness": 3},
                caption_model_processor=self.caption_model_processor,
                ocr_text=[],
                use_local_semantics=True
            )
            
            if result is None:
                parsed_content_list = []
            elif isinstance(result, tuple) and len(result) >= 3:
                parsed_content_list = result[2]
            else:
                parsed_content_list = result
                
        except Exception as fallback_e:
            print(f"Primary OmniParser call failed: {fallback_e}, trying fallback...")
            try:
                result = self.get_som_labeled_img(
                    image_path,
                    self.som_model,
                    BOX_TRESHOLD=0.05,
                    output_coord_in_ratio=True,
                    ocr_bbox=[],
                    ocr_text=[],
                    caption_model_processor=self.caption_model_processor
                )
                if isinstance(result, tuple) and len(result) >= 3:
                    parsed_content_list = result[2]
                else:
                    parsed_content_list = result
            except Exception as e:
                print(f"Fallback OmniParser call failed: {e}")
                parsed_content_list = []
                
        latency = time.time() - start_time
        print(f"OmniParser parsing took {latency:.2f} seconds.")
        
        return parsed_content_list, latency
