$(document).ready(function(){
    // Initialize timeline slider
    $(".timeline-slider .owl-carousel").owlCarousel({
        loop: true,
        margin: 20,
        nav: false,
        dots: false,
        responsive: {
            0: {
                items: 1
            },
            768: {
                items: 2
            },
            992: {
                items: 3
            }
        }
    });
    
    // Initialize team slider
    $(".team-slider .owl-carousel").owlCarousel({
        loop: true,
        margin: 20,
        nav: false,
        dots: false,
        responsive: {
            0: {
                items: 1
            },
            576: {
                items: 2
            },
            992: {
                items: 3
            }
        }
    });
    
    // Custom navigation for timeline slider
    $(".next-timeline").click(function(){
        $(".timeline-slider .owl-carousel").trigger("next.owl.carousel");
    });
    $(".prev-timeline").click(function(){
        $(".timeline-slider .owl-carousel").trigger("prev.owl.carousel");
    });
    
    // Custom navigation for team slider
    $(".next-team").click(function(){
        $(".team-slider .owl-carousel").trigger("next.owl.carousel");
    });
    $(".prev-team").click(function(){
        $(".team-slider .owl-carousel").trigger("prev.owl.carousel");
    });
    
    // Smooth scrolling for anchor links
    $('a[href*="#"]').on('click', function(e) {
        e.preventDefault();
        $('html, body').animate(
            {
                scrollTop: $($(this).attr('href')).offset().top - 80,
            },
            500,
            'linear'
        );
    });
});