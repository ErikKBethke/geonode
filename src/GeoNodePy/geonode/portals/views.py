import json

from django.forms.formsets import formset_factory
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.models import Site

from geonode.maps.models import Layer
from .forms import (DocumentForm, LinkForm,
    PortalForm, PortalContextItemForm, PortalMapForm)
from .models import Portal, PortalMap  # PortalContextItem


def get_portal(kwargs):
    if kwargs.get("slug"):
        portal = get_object_or_404(Portal, slug=kwargs.get("slug"))
    else:
        site = Site.objects.get_current()
        portal = get_object_or_404(Portal, site__pk=site.pk)

    return portal


def portals(request):

    return render_to_response("portals/portal_list.html",
        {"portal_list": Portal.objects.all()},
        context_instance=RequestContext(request)
    )


def index(request, **kwargs):
    """
    Portal Index

    Summary
    Featured Maps
    Full list of maps & datasets
    Documents & links

    Staff will be able to:
    - Add new docs and links
    - Add a new map or dataset, demote a featured map, feature a new map
    - Edit additional info (see portal_edit view)

    """
    portal = get_portal(kwargs)

    request.session["active_portal"] = portal

    featured_maps = PortalMap.objects.filter(portal=portal, featured=True)
    maps = PortalMap.objects.filter(portal=portal, featured=False)

    # @@ Featured Maps, all maps and datasets, documents, links

    # @@ In-page forms (for admins): upload documents, add links

    # @@ Available: add map, dataset, demote featured map, feature map

    return render_to_response("portals/index.html",
        {
            "portal": portal,
            "featured_maps": featured_maps,
            "maps": maps
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_create(request):
    if request.method == "POST":
        form = PortalForm(request.POST, request.FILES)
        if form.is_valid():
            portal = form.save()
            return redirect(portal)

    else:
        form = PortalForm()

    return render_to_response("portals/portal_form.html",
        {"form": form},
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_edit(request, pk):
    """
    Edit Portal

    Most actions are available from detail page (adding maps, links, docs, etc)
    The edit page should allow:
    - Change name
    - Change logos/colors
    - Change navigation items

    """
    portal = get_object_or_404(Portal, pk=pk)

    if request.method == "POST":
        form = PortalForm(request.POST, request.FILES, instance=portal)
        if form.is_valid():
            form.save()
            return redirect("portals_list")

    else:
        form = PortalForm(instance=portal)

    return render_to_response("portals/portal_form.html",
        {"form": form, "portal": portal},
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_customize(request, slug):
    portal = get_object_or_404(Portal, slug=slug)
    ItemFormSet = formset_factory(PortalContextItemForm, extra=0)

    if request.method == "POST":
        formset = ItemFormSet(request.POST)
        if formset.is_valid():
            for form in formset.forms:
                if form.is_valid():
                    form.save(portal)

            portal.save_css()

            return redirect("portals_detail", portal.slug)

    else:
        formset = ItemFormSet(initial=[
            {"name": "font-family", "value": portal.get_context_value("font-family")},
            {"name": "body background-color", "value": portal.get_context_value("body background-color")},
            {"name": "body font-color", "value": portal.get_context_value("body font-color")},
            {"name": "header background-color", "value": portal.get_context_value("header background-color")},
            {"name": "header background-image", "value": portal.get_context_value("header background-image")},
            {"name": "nav background-color", "value": portal.get_context_value("nav background-color")},
            {"name": "nav font-color", "value": portal.get_context_value("nav font-color")},
        ])

    return render_to_response("portals/portal_customize.html",
        {"formset": formset, "portal": portal},
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_map(request, **kwargs):

    portal = get_portal(kwargs)

    if request.method == "POST":
        form = PortalMapForm(request.POST, portal=portal)
        if form.is_valid():
            portalmap = form.save()
            if request.POST.get("featured"):
                portalmap.featured = True
                portalmap.save()
            m = {
                "title": portalmap.map.title,
                "url": portalmap.map.get_absolute_url(),
                "featured": portalmap.featured
            }
            if request.is_ajax():
                return HttpResponse(json.dumps({"map": m}), mimetype="application/javascript")
            else:
                return redirect(portal.get_absolute_url())

    else:
        form = PortalMapForm(portal=portal)
        print form.fields["portal"]

    return render_to_response("portals/map_add.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_remove_map(request, map_pk, **kwargs):

    portal = get_portal(kwargs)
    map = get_object_or_404(PortalMap.objects.filter(portal=portal), map__pk=map_pk)

    if request.method == "POST":
        map.delete()
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/map_remove.html",
        {
            "portal": portal,
            "map": map.map
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_dataset(request, **kwargs):

    portal = get_portal(kwargs)
    datasets = Layer.objects.exclude(pk__in=[d.pk for d in portal.datasets.all()])

    if request.method == "POST":
        dataset = get_object_or_404(
            datasets,
            pk=request.POST.get("dataset")
        )
        portal.datasets.add(dataset)
        d = {
            "title": dataset.title,
            "url": dataset.get_absolute_url()
        }
        if request.is_ajax():
            return HttpResponse(json.dumps({"dataset": d}), mimetype="application/javascript")
        else:
            return redirect(portal.get_absolute_url())

    return render_to_response("portals/dataset_add.html",
        {
            "portal": portal,
            "datasets": datasets
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_remove_dataset(request, dataset_pk, **kwargs):

    portal = get_portal(kwargs)
    dataset = get_object_or_404(portal.datasets, pk=dataset_pk)

    if request.method == "POST":
        portal.datasets.remove(dataset)
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/dataset_remove.html",
        {
            "portal": portal,
            "dataset": dataset
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_link(request, **kwargs):

    portal = get_portal(kwargs)

    if request.method == "POST":
        form = LinkForm(request.POST, portal=portal)
        if form.is_valid():
            link = form.save()
            if request.is_ajax():
                l = {
                    "label": link.label,
                    "url": link.link
                    }
                return HttpResponse(json.dumps({"link": l}), mimetype="application/javascript")
            else:
                return redirect(portal.get_absolute_url())
    else:
        form = LinkForm(portal=portal)

    return render_to_response("portals/link_add.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_delete_link(request, link_pk, **kwargs):

    portal = get_portal(kwargs)
    link = get_object_or_404(portal.links, pk=link_pk)

    if request.method == "POST":
        link.delete()
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/link_delete.html",
        {
            "portal": portal,
            "link": link
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_add_document(request, **kwargs):

    portal = get_portal(kwargs)

    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES, portal=portal)
        if form.is_valid():
            document = form.save()
            if request.is_ajax():
                l = {
                    "label": document.label,
                    "file": document.get_file_url()
                    }
                return HttpResponse(json.dumps({"document": l}), mimetype="application/javascript")
            else:
                return redirect(portal.get_absolute_url())
    else:
        form = DocumentForm(portal=portal)

    return render_to_response("portals/document_add.html",
        {
            "portal": portal,
            "form": form
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def portal_delete_document(request, document_pk, **kwargs):

    portal = get_portal(kwargs)
    document = get_object_or_404(portal.documents, pk=document_pk)

    if request.method == "POST":
        document.delete()
        return redirect(portal.get_absolute_url())

    return render_to_response("portals/document_delete.html",
        {
            "portal": portal,
            "document": document
        },
        context_instance=RequestContext(request)
    )
