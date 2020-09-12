import copy

from dashboard.models import Podcast

def create_inline_styles_element(styles):
    if not styles:
        return None
    element = 'style="'
    for k, v in styles.items():
        element += '%s:%s; ' % (k,v)
    element += '"'
    return element

def get_templates(podcast, episode, target_template=None):

    RADIAL_GRADIENT = 'radial-gradient(90% 81%, rgba(0,0,0,0) 64%, rgba(0,0,0,1) 100%)'
    PRIMARY_COLOR = podcast.primary_color
    SECONDARY_COLOR = podcast.secondary_color

    ASPECT_RATIO = 16/9

    PADDING_BASE = 4
    LOGO_SIZE = '50%'
    PADDING = '%s%%' % PADDING_BASE
    V_POSITION = '%s%%' % (PADDING_BASE * 2)
    H_POSITION = 'calc(%s / %s)' % (V_POSITION, ASPECT_RATIO)

    PADDING_MAX_HEIGHT = '%s%%' % (100 - (PADDING_BASE * 4))

    SMALL_FONT = '1em'
    HUGE_FONT = '3em'

    EPISODE_IMAGE = 'url(/image-proxy/?url=%s)' % episode.image
    if not episode.image_path:
        EPISODE_IMAGE = 'url(/image-proxy/?url=%s)' % podcast.image_path
    PODCAST_IMAGE = 'url(/image-proxy/?url=%s)' % podcast.image_path
    PODCAST_IMAGE_BLUR = 'url(/image-proxy/?url=%s)' % (podcast.blur_image_path if podcast.blur_image_path else podcast.image_path)
    # PODCAST_IMAGE_BLUR = PODCAST_IMAGE

    PODART_TEMPLATE_LIST = {

        'theme-9': {
            'default_design': {
                'text_container': {
                    'styles': {
                        'display': 'flex',
                        'flex-wrap': 'wrap',
                        'height': '100%',
                        'color': SECONDARY_COLOR,
                        'background': PRIMARY_COLOR,
                        'padding': PADDING,
                    },
                },
                'logo': {
                    'src': podcast.logo_path,
                    'styles': {
                        'max-width': LOGO_SIZE,
                        'bottom': V_POSITION,
                        'right': H_POSITION,
                        'z-index': '10',
                    },
                },
                'episode_number': {
                    'styles': {
                        'order': '2',
                        'align-self': 'flex-end',
                    },
                },
                'episode_text': {
                    'styles': {
                        'order': '1',
                        'font-size': '1.5em',
                        'font-weight': '700',
                    },
                },
            },
            'variants': [
                {
                    'design_overides': {

                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'display': 'block',
                            'width': '100%',
                        },
                        'text_container': {
                            'text-align': 'left',
                            'top': 'unset',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'flex-direction': 'row',
                            'flex-wrap': 'nowrap',
                            'text-align': 'left',
                            'top': 'unset',
                        },
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'position': 'absolute',
                            'right': H_POSITION,
                            'bottom': V_POSITION,
                            'text-align': 'right',
                        },
                        'episode_text': {
                            'color': SECONDARY_COLOR,
                            'font-size': '1.4em',
                            'font-weight': '700',
                        },
                        'logo': {
                            'left': H_POSITION,
                            'right': 'unset',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'flex-direction': 'row',
                            'flex-wrap': 'nowrap',
                            'text-align': 'left',
                            'top': 'unset',
                            'padding-bottom': '0',
                        },
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'font-size': HUGE_FONT,
                            'font-weight': '700',
                            'position': 'absolute',
                            'right': H_POSITION,
                            'bottom': '0',
                        },
                        'episode_text': {
                            'color': SECONDARY_COLOR,
                            'font-size': '1.4em',
                            'font-weight': '700',
                        },
                        'logo': {
                            'display': 'none',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                    }
                },
            ]
        },
        'theme-1': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': PODCAST_IMAGE,
                    }
                },
                'text_container': {
                    'styles': {
                        'background': 'black',
                        'color': 'white',
                        'position': 'absolute',
                        'bottom': 0,
                        'left': 0,
                        'right': 0,
                        'top': 'unset',
                        'padding': PADDING,
                        'text-align': 'center',
                        'text-transform': 'uppercase',
                    }
                },
                'episode_text': {
                    'styles': {
                        'color': 'white',
                        'font-weight': '500',
                    }
                },
                'episode_number': {
                    'styles': {
                        'font-size': '.6em',
                        'color': 'white',
                        'font-weight': '300',
                    }
                }
            },
            'variants': [
                {
                    'design_overides': {
                        'episode_text': {
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'text-align': 'left',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'background': 'transparent',
                            'text-align': 'left',
                        },
                    }
                },
            ],
        },

        'theme-1a': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': PODCAST_IMAGE_BLUR,
                        'filter': 'brightness(0.5)',
                    }
                },
                'mask': {
                    'styles' : {
                        'backdrop-filter': 'blur(10px)',
                    }
                },
                'second_cover': {
                    'src': podcast.image_path,
                    'styles': {
                        'max-height': '%s !important' % PADDING_MAX_HEIGHT,
                        'max-width': 'unset !important',
                        'top': V_POSITION,
                        'left': H_POSITION,
                        'bottom': V_POSITION,
                        'box-shadow': '0 0 50px rgba(0,0,0,.7)',
                    }
                },
                'text_container': {
                    'styles': {
                        'background': 'transparent',
                        'color': 'white',
                        'position': 'absolute',
                        'right': H_POSITION,
                        'padding-right': PADDING,
                        'top': V_POSITION,
                        'width': '40%',
                        'left': 'unset',
                        'text-align': 'left',
                        'text-transform': 'uppercase',
                    }
                },
                'episode_text': {
                    'styles': {
                        'color': 'white',
                        'font-weight': '500',
                    }
                },
                'episode_number': {
                    'styles': {
                        'font-size': '.6em',
                        'color': 'white',
                        'font-weight': '300',
                    }
                }
            },
            'variants': [
                {
                    'design_overides': {
                        'episode_text': {
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'text-align': 'left',
                        },
                        'second_cover': {
                            'max-height': '100%',
                            'top': 0,
                            'left': 0,
                            'bottom': 0,
                            'box-shadow': 'none',
                        },
                        'text_container': {
                            'width': '35%',
                        },
                    }
                },
                {
                    'design_overides': {
                        'second_cover': {
                            'max-height': '60% !important',
                            'top': '10%',
                            'left': '32%',
                            'bottom': 'unset',
                        },
                        'text_container': {
                            'color': 'white',
                            'position': 'absolute',
                            'bottom': 0,
                            'left': 0,
                            'right': 0,
                            'top': 'unset',
                            'padding': '2% 4%',
                            'text-align': 'center',
                            'text-transform': 'uppercase',
                            'width': '100%',
                        },
                    }
                },
            ],
        },

        'theme-2': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': EPISODE_IMAGE,
                    }
                },
                'logo': {
                    'src': podcast.logo_path,
                    'styles': {
                        'max-width': LOGO_SIZE,
                        'top': V_POSITION,
                        'right': H_POSITION,
                    }
                },
                'mask': {
                    'styles' : {
                        #'background': RADIAL_GRADIENT,
                    }
                }
            },
            'variants': [
                {
                    'design_overides': {
                    }
                },
                {
                    'design_overides': {
                        'episode_text': {
                            'text-align': 'right',
                            'position': 'absolute',
                            'bottom': V_POSITION,
                            'right': H_POSITION,
                            'color': SECONDARY_COLOR,
                        },
                    }
                },
                {
                    'design_overides': {
                        'episode_number': {
                            'position': 'absolute',
                            'top': V_POSITION,
                            'left': H_POSITION,
                            'color': SECONDARY_COLOR,
                            'background': PRIMARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                        },
                    }
                },
                {
                    'design_overides': {
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'background': PRIMARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'display': 'inline-block',
                        },
                        'episode_text': {
                            'color': SECONDARY_COLOR,
                            'display': 'inline-block',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '700',
                        },
                        'text_container': {
                            'text-align': 'left',
                            'top': 'unset',
                            'padding': PADDING,
                        },
                    }
                },
            ],
        },


        'theme-3': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': EPISODE_IMAGE,
                        'filter': 'grayscale(100%)',
                    }
                },
                'text_container': {
                    'styles': {
                        'text-align': 'center',
                        'top': 'unset',
                        'padding': '6% 4%',
                        'color': SECONDARY_COLOR,
                    }
                },
                'mask': {
                    'styles': {
                        'background-color': PRIMARY_COLOR,
                        'opacity': '.6',
                    }
                },
                'logo': {
                    'src': podcast.logo_path,
                    'styles': {
                        'max-width': LOGO_SIZE,
                        'top': V_POSITION,
                        'right': H_POSITION,
                    }
                },
            },
            'variants': [
                {
                    'design_overides': {
                        'episode_text': {
                            'font-weight': 'bold',
                            'text-transform': 'uppercase',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'padding': '0',
                        },
                        'episode_number': {
                            'font-size': HUGE_FONT,
                            'font-weight': '700',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'padding': '0 5%',
                            'text-align': 'right',
                        },
                        'episode_number': {
                            'font-size': HUGE_FONT,
                            'font-weight': '700',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'episode_number': {
                            'color': PRIMARY_COLOR,
                            'background': SECONDARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'left': '0',
                            'top': '0',
                            'position': 'absolute',
                        },
                        'episode_text': {
                            'text-transform': 'uppercase',
                            'font-weight': '600',
                            'right': H_POSITION,
                            'bottom': V_POSITION,
                            'position': 'absolute',
                        },
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        },
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'background': PRIMARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'left': '0',
                            'top': '0',
                            'position': 'absolute',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        },
                        'episode_text': {
                            'position': 'absolute',
                            'text-align': 'center',
                            'left': '0',
                            'right': '0',
                            'top': '50%',
                            'font-size': '1.5em',
                            'font-weight': '700',
                            'line-height': '1',
                            'margin-top': '-.5em',
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': PADDING,
                            'display': 'flex',
                            'flex-direction': 'column',
                            'height': '100%',
                            'justify-content': 'space-between',
                        },
                        'podcast_name': {
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'order': '1',
                        },
                        'episode_text': {
                            'text-align': 'center',
                            'font-size': '1.5em',
                            'font-weight': '700',
                            'order': '2',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                        'episode_number': {
                            'color': PRIMARY_COLOR,
                            'background': SECONDARY_COLOR,
                            'padding': '5% 6%',
                            'font-size': '2em',
                            'font-weight': '600',
                            'display': 'inline',
                            'border-radius': '150px',
                            'margin': '0 auto',
                            'order': '3',
                        },
                        'logo': {
                            'display': 'none',
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'text-align': 'left',
                            'padding': PADDING,
                            'display': 'flex',
                            'flex-direction': 'column',
                        },
                        'podcast_name': {
                            'order': '3',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                        },
                        'episode_text': {
                            'order': '2',
                            'font-size': '1.5em',
                            'font-weight': '500',
                            'color': SECONDARY_COLOR,
                        },
                        'episode_number': {
                            'order': '1',
                            'font-size': SMALL_FONT,
                            'text-transform': 'uppercase',
                        },
                    }
                },
            ],
        },

        'theme-4': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': EPISODE_IMAGE,
                        'filter': 'grayscale(100%)',
                    }
                },
                'text_container': {
                    'styles': {
                        'text-align': 'center',
                        'top': 'unset',
                        'padding': '6% 4%',
                        'color': PRIMARY_COLOR,
                    }
                },
                'mask': {
                    'styles': {
                        'background-color': '#000000',
                        'opacity': '.2',
                    }
                },
                'logo': {
                    'src': podcast.logo_path,
                    'styles': {
                        'max-width': LOGO_SIZE,
                        'top': V_POSITION,
                        'right': H_POSITION,
                    }
                },
            },
            'variants': [
                {
                    'design_overides': {
                        'episode_text': {
                            'font-weight': 'bold',
                            'text-transform': 'uppercase',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'padding': '0',
                        },
                        'episode_number': {
                            'font-size': HUGE_FONT,
                            'font-weight': '700',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'padding': '0 5%',
                            'text-align': 'right',
                        },
                        'episode_number': {
                            'font-size': HUGE_FONT,
                            'font-weight': '700',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'episode_number': {
                            'color': PRIMARY_COLOR,
                            'background': SECONDARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'left': '0',
                            'top': '0',
                            'position': 'absolute',
                        },
                        'episode_text': {
                            'text-transform': 'uppercase',
                            'font-weight': '600',
                            'right': H_POSITION,
                            'bottom': V_POSITION,
                            'position': 'absolute',
                        },
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        },
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'background': PRIMARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'left': '0',
                            'top': '0',
                            'position': 'absolute',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        },
                        'episode_text': {
                            'position': 'absolute',
                            'text-align': 'center',
                            'left': '0',
                            'right': '0',
                            'top': '50%',
                            'font-size': '1.5em',
                            'font-weight': '700',
                            'line-height': '1',
                            'margin-top': '-.5em',
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': PADDING,
                            'display': 'flex',
                            'flex-direction': 'column',
                            'height': '100%',
                            'justify-content': 'space-between',
                        },
                        'podcast_name': {
                            'text-transform': 'uppercase',
                            'color': SECONDARY_COLOR,
                            'font-size': SMALL_FONT,
                            'order': '1',
                        },
                        'episode_text': {
                            'text-align': 'center',
                            'font-size': '1.5em',
                            'font-weight': '700',
                            'order': '2',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                        'episode_number': {
                            'background': PRIMARY_COLOR,
                            'color': SECONDARY_COLOR,
                            'padding': '5% 6%',
                            'font-size': '2em',
                            'font-weight': '600',
                            'display': 'inline',
                            'border-radius': '150px',
                            'margin': '0 auto',
                            'order': '3',
                        },
                        'logo': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'text-align': 'left',
                            'padding': PADDING,
                            'display': 'flex',
                            'flex-direction': 'column',
                            'color': 'white',
                        },
                        'podcast_name': {
                            'order': '3',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                        },
                        'episode_text': {
                            'order': '2',
                            'font-size': '1.5em',
                            'font-weight': '500',
                            'color': PRIMARY_COLOR,
                        },
                        'episode_number': {
                            'order': '1',
                            'font-size': SMALL_FONT,
                            'text-transform': 'uppercase',
                        },
                    }
                },
            ],
        },

        'theme-4-white': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': EPISODE_IMAGE,
                        'filter': 'grayscale(100%)',
                    }
                },
                'text_container': {
                    'styles': {
                        'text-align': 'center',
                        'top': 'unset',
                        'padding': '6% 4%',
                        'color': PRIMARY_COLOR,
                    }
                },
                'mask': {
                    'styles': {
                        'background-color': '#FFFFFF',
                        'opacity': '.7',
                    }
                },
                'logo': {
                    'src': podcast.logo_path,
                    'styles': {
                        'max-width': LOGO_SIZE,
                        'top': V_POSITION,
                        'right': H_POSITION,
                    }
                },
            },
            'variants': [
                {
                    'design_overides': {
                        'episode_text': {
                            'font-weight': 'bold',
                            'text-transform': 'uppercase',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'padding': '0',
                        },
                        'episode_number': {
                            'font-size': HUGE_FONT,
                            'font-weight': '700',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'padding': '0 5%',
                            'text-align': 'right',
                        },
                        'episode_number': {
                            'font-size': HUGE_FONT,
                            'font-weight': '700',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'episode_number': {
                            'color': PRIMARY_COLOR,
                            'background': SECONDARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'left': '0',
                            'top': '0',
                            'position': 'absolute',
                        },
                        'episode_text': {
                            'text-transform': 'uppercase',
                            'font-weight': '600',
                            'right': H_POSITION,
                            'bottom': V_POSITION,
                            'position': 'absolute',
                        },
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        },
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'background': PRIMARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'left': '0',
                            'top': '0',
                            'position': 'absolute',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': '0',
                        },
                        'episode_text': {
                            'position': 'absolute',
                            'text-align': 'center',
                            'left': '0',
                            'right': '0',
                            'top': '50%',
                            'font-size': '1.5em',
                            'font-weight': '700',
                            'line-height': '1',
                            'margin-top': '-.5em',
                        }
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'top': '0',
                            'padding': PADDING,
                            'display': 'flex',
                            'flex-direction': 'column',
                            'height': '100%',
                            'justify-content': 'space-between',
                        },
                        'podcast_name': {
                            'text-transform': 'uppercase',
                            'color': SECONDARY_COLOR,
                            'font-size': SMALL_FONT,
                            'order': '1',
                        },
                        'episode_text': {
                            'text-align': 'center',
                            'font-size': '1.5em',
                            'font-weight': '700',
                            'order': '2',
                        },
                        'episode_number_label': {
                            'display': 'none',
                        },
                        'episode_number': {
                            'background': PRIMARY_COLOR,
                            'color': SECONDARY_COLOR,
                            'padding': '5% 6%',
                            'font-size': '2em',
                            'font-weight': '600',
                            'display': 'inline',
                            'border-radius': '150px',
                            'margin': '0 auto',
                            'order': '3',
                        },
                        'logo': {
                            'display': 'none',
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'text-align': 'left',
                            'padding': PADDING,
                            'display': 'flex',
                            'flex-direction': 'column',
                            'color': 'black',
                        },
                        'podcast_name': {
                            'order': '3',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                        },
                        'episode_text': {
                            'order': '2',
                            'font-size': '1.5em',
                            'font-weight': '500',
                            'color': PRIMARY_COLOR,
                        },
                        'episode_number': {
                            'order': '1',
                            'font-size': SMALL_FONT,
                            'text-transform': 'uppercase',
                        },
                    }
                },
            ],
        },

        'theme-5': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': EPISODE_IMAGE,
                    }
                },
                'text_container': {
                    'styles': {
                        'display': 'flex',
                        'flex-wrap': 'wrap',
                        'height': '100%',
                        'color': SECONDARY_COLOR,
                    },
                },
                'mask': {
                    'styles' : {
                        #'background': RADIAL_GRADIENT,
                    }
                }
            },
            'variants': [
                {
                    'design_overides': {
                        'mask': {
                            'border': '1.2em solid ' + PRIMARY_COLOR,
                        },
                        'text_container': {
                            'text-transform': 'uppercase',
                            'line-height': '1',
                            'padding': '.35em',
                            'font-size': '.8em',
                        },
                        'episode_number': {
                            'align-self': 'flex-start',
                        },
                        'episode_text': {
                            'align-self': 'flex-end',
                            'text-align': 'right',
                            'width': '100%',
                            'line-height': '.8',
                        },
                    }
                },
                {
                    'design_overides': {
                        'episode_text': {
                            'background': PRIMARY_COLOR,
                            'align-self': 'flex-end',
                            'text-align': 'center',
                            'width': '100%',
                            'text-transform': 'uppercase',
                            'padding': '1% 0',
                        },
                    }
                },
                {
                    'design_overides': {
                        'episode_number_label': {
                            'display': 'none',
                        },
                        'episode_number': {
                            'position': 'absolute',
                            'top': V_POSITION,
                            'right': H_POSITION,
                            'color': PRIMARY_COLOR,
                            'font-size': HUGE_FONT,
                            'font-weight': '600',
                        },
                        'episode_text': {
                            'background': PRIMARY_COLOR,
                            'align-self': 'flex-end',
                            'text-align': 'center',
                            'width': '100%',
                            'text-transform': 'uppercase',
                            'padding': '1% 0',
                        },
                    }
                },
                {
                    'design_overides': {
                        'mask': {
                            'border': '1.2em solid white',
                        },
                        'text_container': {
                            'text-transform': 'uppercase',
                            'line-height': '1',
                            'padding': '.35em',
                            'font-size': '.8em',
                            'color': PRIMARY_COLOR,
                        },
                        'episode_number': {
                            'align-self': 'flex-start',
                        },
                        'episode_text': {
                            'align-self': 'flex-end',
                            'text-align': 'right',
                            'width': '100%',
                            'line-height': '.8',
                        },
                    }
                },

            ],
        },
        'theme-6': {
            'default_design': {
                'image': {
                    'styles': {
                        'background-image': EPISODE_IMAGE,
                    }
                },
                'text_container': {
                    'styles': {
                        'display': 'flex',
                        'flex-wrap': 'wrap',
                        'height': '100%',
                        'color': SECONDARY_COLOR,
                    },
                },
                'mask': {
                    'styles' : {
                        #'background': RADIAL_GRADIENT,
                    }
                }
            },
            'variants': [
                {
                    'design_overides': {
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'background': PRIMARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'display': 'inline-block',
                        },
                        'text_container': {
                            'text-align': 'left',
                            'top': 'unset',
                            'padding': PADDING,
                        },
                    }
                },
                {
                    'design_overides': {
                        'text_container': {
                            'flex-direction': 'row',
                            'flex-wrap': 'nowrap',
                            'text-align': 'left',
                            'top': 'unset',
                            'padding': PADDING,
                        },
                        'episode_number': {
                            'color': SECONDARY_COLOR,
                            'background': PRIMARY_COLOR,
                            'padding': '2px 5px',
                            'text-transform': 'uppercase',
                            'font-size': SMALL_FONT,
                            'font-weight': '600',
                            'display': 'inline-block',
                        },
                        'episode_text': {
                            'color': PRIMARY_COLOR,
                            'font-size': '1.4em',
                            'padding-left': PADDING,
                            'font-weight': '700',
                            'align-self': 'flex-end',
                        },
                    }
                },

            ]
        },


    }

    themes = []
    for theme_name, theme_settings in PODART_TEMPLATE_LIST.items():

        # put theme defaults
        default_design = theme_settings['default_design']
        variants = theme_settings['variants']

        design_options = []

        # loop through variants
        for variant in variants:

            variant_design = copy.deepcopy(default_design)

            # override any theme defaults
            if 'design_overides' in variant:
                for section, overrides in variant['design_overides'].items():
                    for k,v in overrides.items():
                        if section not in variant_design:
                            variant_design[section] =  {'styles':{}}
                        variant_design[section]['styles'][k] = v

            # create styles= and style json for use in template
            design_option_settings = {}
            for key, values in variant_design.items():
                design_option_settings[key] = values
                if 'styles' in values:
                    design_option_settings[key]['style_tag'] = create_inline_styles_element(values['styles'])

            design_options.append(design_option_settings)

        themes.append(design_options)

    if target_template:
        target_theme = int(target_template.split('-')[0])
        target_variant = int(target_template.split('-')[1])
        try:
            themes = [[themes[target_theme][target_variant],]]
        except IndexError:
            pass

    return themes

def get_episode_template(podcast, episode):
    if episode.template:
        theme = get_templates(podcast, episode, target_template=episode.template)
        return theme[0][0]
    return None